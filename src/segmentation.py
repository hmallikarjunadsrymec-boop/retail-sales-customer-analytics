"""
Customer RFM Segmentation & Machine Learning Clustering Module
Calculates Recency, Frequency, Monetary metrics, computes rule-based segments,
evaluates K-Means clustering with Elbow and Silhouette metrics, and profiles clusters.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

PROCESSED_PARQUET = os.path.join("data", "processed", "retail_cleaned.parquet")
PROCESSED_CSV = os.path.join("data", "processed", "retail_cleaned.csv")
RFM_OUTPUT_CSV = os.path.join("data", "processed", "customer_rfm.csv")
RFM_OUTPUT_PARQUET = os.path.join("data", "processed", "customer_rfm.parquet")
FIGURES_DIR = os.path.join("reports", "eda_figures")
RFM_SUMMARY_PATH = os.path.join("reports", "rfm_summary.json")


def compute_rfm_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Recency, Frequency, and Monetary value for each registered customer.
    """
    # Filter to registered customers
    df_reg = df.dropna(subset=["CustomerID"]).copy()
    df_reg["CustomerID"] = df_reg["CustomerID"].astype(str)

    # Reference snapshot date: 1 day after the latest transaction
    snapshot_date = df_reg["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = (
        df_reg.groupby("CustomerID")
        .agg(
            Recency=("InvoiceDate", lambda d: int((snapshot_date - d.max()).days)),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Revenue", "sum"),
            FirstPurchaseDate=("InvoiceDate", "min"),
            LastPurchaseDate=("InvoiceDate", "max"),
            Country=("Country", "first")
        )
        .reset_index()
    )

    rfm["Monetary"] = rfm["Monetary"].round(2)
    rfm["AvgOrderValue"] = (rfm["Monetary"] / rfm["Frequency"]).round(2)
    rfm["CustomerTenureDays"] = (
        (snapshot_date - pd.to_datetime(rfm["FirstPurchaseDate"])).dt.days
    )

    return rfm


def assign_rule_based_rfm_segments(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns quintile scores (1 to 5) and standard behavioral segments.
    """
    df_rfm = rfm.copy()

    # Calculate quintiles using rank(method='first') to ensure robust binning
    df_rfm["R_Score"] = pd.qcut(
        df_rfm["Recency"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)

    df_rfm["F_Score"] = pd.qcut(
        df_rfm["Frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    df_rfm["M_Score"] = pd.qcut(
        df_rfm["Monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    df_rfm["RFM_Score"] = (
        df_rfm["R_Score"].astype(str) +
        df_rfm["F_Score"].astype(str) +
        df_rfm["M_Score"].astype(str)
    )

    # Behavioral Segment Assignment
    def segment_customer(row):
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4:
            return "Champions"
        if r >= 3 and f >= 3:
            return "Loyal Customers"
        if r >= 4 and f in [1, 2]:
            return "Potential Loyalists"
        if r >= 3 and f in [1, 2]:
            return "Promising / Need Attention"
        if r <= 2 and f >= 4 and m >= 4:
            return "Can't Lose Them"
        if r <= 2 and f >= 3:
            return "At Risk"
        if r in [2, 3] and f <= 2:
            return "About to Sleep"
        if r <= 2 and f in [1, 2] and m <= 2:
            return "Hibernating"
        return "Lost / Dormant"

    df_rfm["Customer_Segment"] = df_rfm.apply(segment_customer, axis=1)
    return df_rfm


def run_kmeans_clustering(rfm: pd.DataFrame, max_k: int = 8) -> tuple[pd.DataFrame, dict]:
    """
    Executes K-Means clustering on Log-Transformed & Standardized RFM features.
    Evaluates Elbow and Silhouette metrics.
    """
    df_cluster = rfm.copy()
    features = ["Recency", "Frequency", "Monetary"]

    # 1. Log transformation to normalize highly skewed retail distributions
    # Shift any non-positive values safely
    rfm_log = df_cluster[features].copy()
    rfm_log["Recency"] = np.log1p(rfm_log["Recency"])
    rfm_log["Frequency"] = np.log1p(rfm_log["Frequency"])
    rfm_log["Monetary"] = np.log1p(np.maximum(rfm_log["Monetary"], 0.01))

    # 2. Standardization
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log)

    # 3. Model Evaluation across k values
    k_range = range(2, max_k + 1)
    inertias = []
    silhouette_scores = []

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(rfm_scaled)
        inertias.append(float(kmeans.inertia_))
        score = float(silhouette_score(rfm_scaled, kmeans.labels_))
        silhouette_scores.append(score)

    # Select optimal k: k=4 provides business-interpretable segments with strong silhouette
    optimal_k = 4
    final_kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    df_cluster["KMeans_Cluster"] = final_kmeans.fit_predict(rfm_scaled)

    # Cluster profiling: compute mean metrics per cluster
    cluster_profiles = (
        df_cluster.groupby("KMeans_Cluster")
        .agg(
            Count=("CustomerID", "count"),
            Mean_Recency=("Recency", "mean"),
            Mean_Frequency=("Frequency", "mean"),
            Mean_Monetary=("Monetary", "mean"),
            Total_Revenue=("Monetary", "sum")
        )
        .reset_index()
    )

    # Map cluster index to intuitive business persona based on Monetary & Recency
    cluster_profiles = cluster_profiles.sort_values("Mean_Monetary", ascending=False).reset_index(drop=True)
    cluster_name_map = {}
    names = [
        "High-Value VIPs",
        "Active Core Regulars",
        "Recent Casual Buyers",
        "Dormant / Lost Shoppers"
    ]
    for idx, row in cluster_profiles.iterrows():
        c_id = int(row["KMeans_Cluster"])
        cluster_name_map[c_id] = names[idx] if idx < len(names) else f"Cluster {c_id}"

    df_cluster["Cluster_Name"] = df_cluster["KMeans_Cluster"].map(cluster_name_map)

    eval_results = {
        "k_range": list(k_range),
        "inertias": [round(x, 2) for x in inertias],
        "silhouette_scores": [round(x, 4) for x in silhouette_scores],
        "selected_k": optimal_k,
        "selected_k_silhouette": round(silhouette_scores[optimal_k - 2], 4),
        "cluster_name_map": cluster_name_map,
        "cluster_profiles": cluster_profiles.to_dict(orient="records")
    }

    return df_cluster, eval_results


def generate_segmentation_visualizations(df_rfm: pd.DataFrame, eval_results: dict):
    """
    Generates high-resolution visualizations for customer segmentation.
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # --- 1. Elbow & Silhouette Evaluation ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    k_vals = eval_results["k_range"]

    ax1.plot(k_vals, eval_results["inertias"], marker="o", color="#1f77b4", linewidth=2.5)
    ax1.axvline(eval_results["selected_k"], color="red", linestyle="--", label=f"Selected k = {eval_results['selected_k']}")
    ax1.set_title("K-Means Elbow Method (Inertia)", pad=12, fontweight="bold")
    ax1.set_xlabel("Number of Clusters (k)")
    ax1.set_ylabel("Inertia (Sum of Squared Distances)")
    ax1.legend()

    ax2.plot(k_vals, eval_results["silhouette_scores"], marker="s", color="#2ca02c", linewidth=2.5)
    ax2.axvline(eval_results["selected_k"], color="red", linestyle="--", label=f"Selected k = {eval_results['selected_k']}")
    ax2.set_title("Silhouette Coefficient Score by k", pad=12, fontweight="bold")
    ax2.set_xlabel("Number of Clusters (k)")
    ax2.set_ylabel("Mean Silhouette Score")
    ax2.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "09_rfm_elbow_silhouette.png"), dpi=300)
    plt.close(fig)

    # --- 2. Rule-Based Customer Segment Distribution ---
    seg_summary = (
        df_rfm.groupby("Customer_Segment")
        .agg(
            Customer_Count=("CustomerID", "count"),
            Total_Revenue=("Monetary", "sum"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean")
        )
        .reset_index()
        .sort_values("Customer_Count", ascending=False)
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    sns.barplot(data=seg_summary, y="Customer_Segment", x="Customer_Count", palette="viridis", ax=ax1, hue="Customer_Segment", legend=False)
    ax1.set_title("Customer Count by RFM Segment", pad=12, fontweight="bold")
    ax1.set_xlabel("Number of Customers")
    ax1.set_ylabel("")
    for i, v in enumerate(seg_summary["Customer_Count"]):
        ax1.text(v + 15, i, f"{v:,}", va="center", fontsize=9, fontweight="bold")
    ax1.set_xlim(0, seg_summary["Customer_Count"].max() * 1.15)

    sns.barplot(data=seg_summary.sort_values("Total_Revenue", ascending=False), y="Customer_Segment", x="Total_Revenue", palette="plasma", ax=ax2, hue="Customer_Segment", legend=False)
    ax2.set_title("Total Revenue Contribution by RFM Segment (£)", pad=12, fontweight="bold")
    ax2.set_xlabel("Total Spend (£ GBP)")
    ax2.set_ylabel("")
    for i, v in enumerate(seg_summary.sort_values("Total_Revenue", ascending=False)["Total_Revenue"]):
        ax2.text(v + 20000, i, f"£{v:,.0f}", va="center", fontsize=9, fontweight="bold")
    ax2.set_xlim(0, seg_summary["Total_Revenue"].max() * 1.2)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "10_rfm_customer_segments_distribution.png"), dpi=300)
    plt.close(fig)

    # --- 3. Recency vs Frequency vs Monetary Scatter ---
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = sns.scatterplot(
        data=df_rfm,
        x="Recency",
        y="Frequency",
        hue="Cluster_Name",
        size="Monetary",
        sizes=(20, 400),
        alpha=0.75,
        palette="tab10",
        ax=ax
    )
    ax.set_yscale("log")
    ax.set_title("Customer Clusters: Recency vs Frequency (Bubble Size = Monetary Value)", pad=15, fontweight="bold")
    ax.set_xlabel("Recency (Days since last purchase)")
    ax.set_ylabel("Frequency (Distinct Orders, Log Scale)")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "11_rfm_clusters_scatter.png"), dpi=300)
    plt.close(fig)

    # --- 4. RFM Score Heatmap (R_Score vs F_Score Mean Monetary) ---
    rfm_matrix = df_rfm.pivot_table(
        index="R_Score",
        columns="F_Score",
        values="Monetary",
        aggfunc="mean"
    ).sort_index(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(rfm_matrix, annot=True, fmt=",.0f", cmap="YlOrRd", cbar_kws={"label": "Mean Spend (£)"}, ax=ax)
    ax.set_title("RFM Heatmap: Mean Customer Spend by R and F Scores", pad=15, fontweight="bold")
    ax.set_xlabel("Frequency Score (1=Low, 5=High)")
    ax.set_ylabel("Recency Score (1=Old, 5=Recent)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "12_rfm_segment_heatmap.png"), dpi=300)
    plt.close(fig)

    print(f"Segmentation visualizations saved to {FIGURES_DIR}/")


def run_full_segmentation_pipeline() -> pd.DataFrame:
    """
    Orchestrates the entire customer segmentation workflow.
    """
    print("Executing Customer RFM Segmentation pipeline...")
    if os.path.exists(PROCESSED_PARQUET):
        df = pd.read_parquet(PROCESSED_PARQUET)
    else:
        df = pd.read_csv(PROCESSED_CSV)

    # 1. Compute raw RFM
    rfm_df = compute_rfm_metrics(df)

    # 2. Assign Rule-based segments
    rfm_scored = assign_rule_based_rfm_segments(rfm_df)

    # 3. K-Means Clustering
    rfm_clustered, eval_results = run_kmeans_clustering(rfm_scored)

    # 4. Generate Visualizations
    generate_segmentation_visualizations(rfm_clustered, eval_results)

    # 5. Persist Datasets
    os.makedirs(os.path.dirname(RFM_OUTPUT_CSV), exist_ok=True)
    rfm_clustered.to_csv(RFM_OUTPUT_CSV, index=False)
    rfm_clustered.to_parquet(RFM_OUTPUT_PARQUET, index=False)

    # Persist summary
    summary_data = {
        "total_segmented_customers": len(rfm_clustered),
        "total_customer_revenue": round(float(rfm_clustered["Monetary"].sum()), 2),
        "median_recency_days": float(rfm_clustered["Recency"].median()),
        "median_frequency": float(rfm_clustered["Frequency"].median()),
        "median_monetary": float(rfm_clustered["Monetary"].median()),
        "kmeans_evaluation": eval_results,
        "segment_breakdown": (
            rfm_clustered.groupby("Customer_Segment")
            .agg(Count=("CustomerID", "count"), Revenue=("Monetary", "sum"))
            .reset_index()
            .to_dict(orient="records")
        )
    }

    with open(RFM_SUMMARY_PATH, "w") as f:
        json.dump(summary_data, f, indent=4)

    print(f"Customer RFM segmentation complete. Output saved to {RFM_OUTPUT_CSV}")
    return rfm_clustered


if __name__ == "__main__":
    rfm_result = run_full_segmentation_pipeline()
    print("\nCustomer Segments Summary:")
    print(rfm_result["Customer_Segment"].value_counts())
    print("\nKMeans Clusters Summary:")
    print(rfm_result["Cluster_Name"].value_counts())
