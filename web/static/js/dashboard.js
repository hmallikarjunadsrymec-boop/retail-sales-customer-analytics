/**
 * Retail Sales & Customer Analytics Platform
 * Unified Single-Dashboard & Portal Controller (Chart.js)
 */

let charts = {};
let currentFilterCountry = "All";
let currentFilterCategory = "All";
let currentCustomerPage = 1;
let currentProducts = [];

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initFilters();
  loadAllData();
  setupEventListeners();
});

function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

function switchTab(tabId) {
  const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  if (btn) btn.click();
}

function setupEventListeners() {
  document.getElementById("countryFilter").addEventListener("change", (e) => {
    currentFilterCountry = e.target.value;
    loadFilteredData();
  });

  document.getElementById("categoryFilter").addEventListener("change", (e) => {
    currentFilterCategory = e.target.value;
    loadFilteredData();
  });

  document.getElementById("customerSearch").addEventListener("input", () => {
    currentCustomerPage = 1;
    loadCustomersTable();
  });

  document.getElementById("rfmFilterSelect").addEventListener("change", () => {
    currentCustomerPage = 1;
    loadCustomersTable();
  });

  const skuSearch = document.getElementById("skuSearchInput");
  if (skuSearch) {
    skuSearch.addEventListener("input", (e) => {
      filterProductsTable(e.target.value);
    });
  }
}

async function initFilters() {
  try {
    const res = await fetch("/api/filters");
    const data = await res.json();

    const countrySelect = document.getElementById("countryFilter");
    countrySelect.innerHTML = data.countries
      .map((c) => `<option value="${c}">${c === "All" ? "All Countries" : c}</option>`)
      .join("");

    const catSelect = document.getElementById("categoryFilter");
    catSelect.innerHTML = data.categories
      .map((c) => `<option value="${c}">${c === "All" ? "All Categories" : c}</option>`)
      .join("");
  } catch (err) {
    console.error("Failed to load filter dropdowns", err);
  }
}

async function loadAllData() {
  await Promise.all([
    loadKPIs(),
    loadMonthlyTrend(),
    loadCategories(),
    loadTopProducts(),
    loadTopVolumeProducts(),
    loadCountries(),
    loadRFM(),
    loadTemporalDynamics(),
    loadOrderStats(),
    loadCustomersTable()
  ]);
}

async function loadFilteredData() {
  await Promise.all([
    loadKPIs(),
    loadMonthlyTrend(),
    loadTopProducts(),
    loadTopVolumeProducts()
  ]);
}

async function loadKPIs() {
  try {
    const url = `/api/kpis?country=${encodeURIComponent(currentFilterCountry)}&category=${encodeURIComponent(currentFilterCategory)}`;
    const res = await fetch(url);
    const data = await res.json();

    document.getElementById("kpiRevenue").textContent = `£${data.total_revenue.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById("kpiOrders").textContent = data.total_orders.toLocaleString();
    document.getElementById("kpiAOV").textContent = `£${data.overall_aov.toLocaleString("en-GB", { minimumFractionDigits: 2 })}`;
    document.getElementById("kpiCustomers").textContent = data.total_customers.toLocaleString();
    document.getElementById("kpiUnits").textContent = data.total_units_sold.toLocaleString();
    document.getElementById("kpiRepeatRate").textContent = `${data.repeat_rate_pct}%`;

    // Retention Tab Donut
    renderRetentionDonut(data.repeat_customers, data.one_time_customers);
  } catch (err) {
    console.error("Error loading KPIs", err);
  }
}

async function loadMonthlyTrend() {
  try {
    const url = `/api/monthly?country=${encodeURIComponent(currentFilterCountry)}&category=${encodeURIComponent(currentFilterCategory)}`;
    const res = await fetch(url);
    const data = await res.json();

    const labels = data.map((d) => d.year_month);
    const revenues = data.map((d) => d.revenue);
    const orders = data.map((d) => d.orders);

    // 1. Overview Monthly Chart
    renderChart("monthlyChart", {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            type: "bar",
            label: "Revenue (£ GBP)",
            data: revenues,
            backgroundColor: "#2563eb",
            borderRadius: 4,
            yAxisID: "y"
          },
          {
            type: "line",
            label: "Orders",
            data: orders,
            borderColor: "#ea580c",
            backgroundColor: "#ea580c",
            borderWidth: 2.5,
            pointRadius: 3,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: { callback: (v) => `£${(v / 1000).toFixed(0)}k` },
            grid: { color: "#f1f5f9" }
          },
          y1: { position: "right", grid: { drawOnChartArea: false } },
          x: { grid: { display: false } }
        }
      }
    });

    // 2. Sales Tab: MoM Growth Chart
    const momData = data.filter((d) => d.mom_growth_pct !== null);
    renderChart("momGrowthChart", {
      type: "bar",
      data: {
        labels: momData.map((d) => d.year_month),
        datasets: [
          {
            label: "MoM Growth (%)",
            data: momData.map((d) => d.mom_growth_pct),
            backgroundColor: momData.map((d) => (d.mom_growth_pct >= 0 ? "#16a34a" : "#dc2626")),
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: { callback: (v) => `${v}%` },
            grid: { color: "#f1f5f9" }
          },
          x: { grid: { display: false } }
        }
      }
    });

    // Render monthly table in Sales Tab
    const tbody = document.getElementById("monthlyTableBody");
    if (tbody) {
      tbody.innerHTML = data
        .map((r) => `
          <tr>
            <td><strong>${r.year_month}</strong></td>
            <td>£${r.revenue.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</td>
            <td>${r.orders.toLocaleString()}</td>
            <td>${r.customers.toLocaleString()}</td>
            <td>${r.units_sold.toLocaleString()}</td>
            <td>£${r.aov.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</td>
            <td style="color: ${r.mom_growth_pct >= 0 ? '#16a34a' : '#dc2626'}; font-weight: 600;">
              ${r.mom_growth_pct !== null ? (r.mom_growth_pct >= 0 ? '+' : '') + r.mom_growth_pct + '%' : '—'}
            </td>
          </tr>
        `)
        .join("");
    }
  } catch (err) {
    console.error("Error loading monthly trend", err);
  }
}

async function loadCategories() {
  try {
    const res = await fetch("/api/categories");
    const data = await res.json();

    renderChart("categoryChart", {
      type: "doughnut",
      data: {
        labels: data.map((d) => d.category),
        datasets: [
          {
            data: data.map((d) => d.revenue),
            backgroundColor: [
              "#2563eb", "#0ea5e9", "#10b981", "#f59e0b",
              "#8b5cf6", "#ec4899", "#64748b", "#14b8a6"
            ]
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "right" } }
      }
    });

    // Category summary table in Products Tab
    const catTbody = document.getElementById("categoryTableBody");
    if (catTbody) {
      catTbody.innerHTML = data
        .map((c) => `
          <tr>
            <td><strong>${c.category}</strong></td>
            <td>£${c.revenue.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</td>
            <td><strong>${c.share_pct}%</strong></td>
            <td>${c.units_sold.toLocaleString()}</td>
            <td>${c.orders.toLocaleString()}</td>
            <td>£${(c.revenue / c.units_sold).toFixed(2)}</td>
          </tr>
        `)
        .join("");
    }
  } catch (err) {
    console.error("Error loading categories", err);
  }
}

async function loadTopProducts() {
  try {
    const url = `/api/top-products?by=revenue&limit=10&category=${encodeURIComponent(currentFilterCategory)}`;
    const res = await fetch(url);
    const data = await res.json();
    currentProducts = data;

    renderChart("topProductsChart", {
      type: "bar",
      data: {
        labels: data.map((d) => (d.description.length > 22 ? d.description.slice(0, 22) + "..." : d.description)),
        datasets: [
          {
            label: "Gross Revenue (£)",
            data: data.map((d) => d.total_revenue),
            backgroundColor: "#0ea5e9",
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { callback: (v) => `£${(v / 1000).toFixed(0)}k` } }
        }
      }
    });

    renderProductsTable(data);
  } catch (err) {
    console.error("Error loading top products", err);
  }
}

async function loadTopVolumeProducts() {
  try {
    const url = `/api/top-products?by=volume&limit=10&category=${encodeURIComponent(currentFilterCategory)}`;
    const res = await fetch(url);
    const data = await res.json();

    renderChart("topVolumeChart", {
      type: "bar",
      data: {
        labels: data.map((d) => (d.description.length > 22 ? d.description.slice(0, 22) + "..." : d.description)),
        datasets: [
          {
            label: "Units Sold",
            data: data.map((d) => d.total_quantity),
            backgroundColor: "#059669",
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { callback: (v) => `${(v / 1000).toFixed(0)}k` } }
        }
      }
    });
  } catch (err) {
    console.error("Error loading volume products", err);
  }
}

function renderProductsTable(products) {
  const tbody = document.getElementById("productsTableBody");
  if (!tbody) return;
  tbody.innerHTML = products
    .map((p) => `
      <tr>
        <td><code>${p.stock_code}</code></td>
        <td><strong>${p.description}</strong></td>
        <td><span class="badge badge-loyal">${p.category}</span></td>
        <td>£${p.avg_price.toFixed(2)}</td>
        <td>${p.total_quantity.toLocaleString()}</td>
        <td><strong>£${p.total_revenue.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</strong></td>
        <td>${p.order_count.toLocaleString()}</td>
      </tr>
    `)
    .join("");
}

function filterProductsTable(query) {
  if (!query) {
    renderProductsTable(currentProducts);
    return;
  }
  const q = query.toUpperCase();
  const filtered = currentProducts.filter(
    (p) => p.description.toUpperCase().includes(q) || p.stock_code.toUpperCase().includes(q)
  );
  renderProductsTable(filtered);
}

async function loadCountries() {
  try {
    const res = await fetch("/api/countries?limit=6");
    const data = await res.json();

    renderChart("countryChart", {
      type: "bar",
      data: {
        labels: data.map((d) => d.country),
        datasets: [
          {
            label: "Revenue (£)",
            data: data.map((d) => d.revenue),
            backgroundColor: "#10b981",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { ticks: { callback: (v) => `£${(v / 1000).toFixed(0)}k` } }
        }
      }
    });
  } catch (err) {
    console.error("Error loading countries", err);
  }
}

async function loadRFM() {
  try {
    const res = await fetch("/api/rfm");
    const data = await res.json();

    renderChart("rfmChart", {
      type: "bar",
      data: {
        labels: data.segments.map((s) => s.Customer_Segment),
        datasets: [
          {
            label: "Segment Revenue (£)",
            data: data.segments.map((s) => s.Total_Revenue),
            backgroundColor: "#8b5cf6",
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { callback: (v) => `£${(v / 1000).toFixed(0)}k` } }
        }
      }
    });

    // Render RFM Cluster Cards in Segmentation Tab
    const clusterContainer = document.getElementById("kmeansClusterCards");
    if (clusterContainer) {
      clusterContainer.innerHTML = data.clusters
        .map((cl) => `
          <div class="kpi-card" style="border-top: 4px solid var(--primary);">
            <div style="font-size: 0.8rem; font-weight: 700; color: var(--primary); text-transform: uppercase;">Cluster ${cl.KMeans_Cluster}</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: var(--secondary); margin: 0.2rem 0;">${cl.Cluster_Name}</div>
            <div style="font-size: 0.88rem; color: var(--text-muted); margin-top: 0.5rem;">
              • Accounts: <strong>${cl.Accounts.toLocaleString()}</strong><br>
              • Mean Spend: <strong>£${cl.Mean_Spend.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</strong><br>
              • Mean Recency: <strong>${cl.Mean_Recency} days</strong><br>
              • Mean Orders: <strong>${cl.Mean_Frequency}</strong>
            </div>
          </div>
        `)
        .join("");
    }
  } catch (err) {
    console.error("Error loading RFM", err);
  }
}

async function loadTemporalDynamics() {
  try {
    const res = await fetch("/api/dow-hour");
    const data = await res.json();

    // Day of Week Chart
    renderChart("dowChart", {
      type: "bar",
      data: {
        labels: data.day_of_week.map((d) => d.day_of_week),
        datasets: [
          {
            label: "Orders",
            data: data.day_of_week.map((d) => d.orders),
            backgroundColor: "#0284c7",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });

    // Hour of Day Chart
    const hours = data.hours.filter((h) => h.hour >= 6 && h.hour <= 20);
    renderChart("hourChart", {
      type: "line",
      data: {
        labels: hours.map((h) => `${h.hour}:00`),
        datasets: [
          {
            label: "Orders",
            data: hours.map((h) => h.orders),
            borderColor: "#38bdf8",
            backgroundColor: "rgba(56, 189, 248, 0.2)",
            fill: true,
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  } catch (err) {
    console.error("Error loading temporal data", err);
  }
}

async function loadOrderStats() {
  try {
    const res = await fetch("/api/order-distribution");
    const data = await res.json();

    document.getElementById("statMeanAOV").textContent = `£${data.mean_aov.toFixed(2)}`;
    document.getElementById("statMedianAOV").textContent = `£${data.median_aov.toFixed(2)}`;
    document.getElementById("statP75AOV").textContent = `£${data.p75_aov.toFixed(2)}`;
    document.getElementById("statP95AOV").textContent = `£${data.p95_aov.toFixed(2)}`;
  } catch (err) {
    console.error("Error loading order distribution", err);
  }
}

function renderRetentionDonut(repeat, oneTime) {
  renderChart("retentionDonutChart", {
    type: "doughnut",
    data: {
      labels: ["Repeat Customers", "One-Time Buyers"],
      datasets: [
        {
          data: [repeat, oneTime],
          backgroundColor: ["#16a34a", "#dc2626"]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } }
    }
  });
}

async function loadCustomersTable() {
  try {
    const searchVal = document.getElementById("customerSearch").value;
    const segVal = document.getElementById("rfmFilterSelect").value;

    const url = `/api/customers?segment=${encodeURIComponent(segVal)}&search=${encodeURIComponent(searchVal)}&page=${currentCustomerPage}&page_size=15`;
    const res = await fetch(url);
    const result = await res.json();

    const tbody = document.getElementById("customersTableBody");
    tbody.innerHTML = result.data
      .map((c) => {
        let badgeClass = "badge-dormant";
        if (c.Customer_Segment === "Champions") badgeClass = "badge-champions";
        else if (c.Customer_Segment === "Loyal Customers") badgeClass = "badge-loyal";
        else if (c.Customer_Segment.includes("Risk") || c.Customer_Segment.includes("Lose")) badgeClass = "badge-atrisk";

        return `
          <tr>
            <td><strong>#${c.CustomerID}</strong></td>
            <td><span class="badge ${badgeClass}">${c.Customer_Segment}</span></td>
            <td>${c.Cluster_Name}</td>
            <td>${c.Recency} days</td>
            <td>${c.Frequency}</td>
            <td><strong>£${c.Monetary.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</strong></td>
            <td>£${c.AvgOrderValue.toLocaleString("en-GB", { minimumFractionDigits: 2 })}</td>
            <td><code>${c.RFM_Score}</code></td>
            <td>${c.Country}</td>
          </tr>
        `;
      })
      .join("");

    document.getElementById("pageInfo").textContent = `Page ${result.page} of ${result.total_pages || 1} (${result.total_records.toLocaleString()} accounts)`;
    document.getElementById("prevPageBtn").disabled = result.page <= 1;
    document.getElementById("nextPageBtn").disabled = result.page >= result.total_pages;
  } catch (err) {
    console.error("Error loading customers table", err);
  }
}

function changePage(delta) {
  currentCustomerPage += delta;
  loadCustomersTable();
}

function exportCurrentCustomers() {
  window.open("/api/customers?page=1&page_size=1000", "_blank");
}

function renderChart(elementId, config) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const ctx = el.getContext("2d");
  if (charts[elementId]) {
    charts[elementId].destroy();
  }
  charts[elementId] = new Chart(ctx, config);
}
