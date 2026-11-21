/**
 * Retail Sales & Customer Analytics Platform
 * Interactive Dashboard Frontend Controller (Chart.js)
 */

let monthlyChart = null;
let categoryChart = null;
let topProductsChart = null;
let rfmChart = null;
let countryChart = null;

let currentFilterCountry = "All";
let currentFilterCategory = "All";
let currentPage = 1;

document.addEventListener("DOMContentLoaded", () => {
  initFilters();
  loadAllDashboardData();
  setupEventListeners();
});

function setupEventListeners() {
  document.getElementById("countryFilter").addEventListener("change", (e) => {
    currentFilterCountry = e.target.value;
    loadAllDashboardData();
  });

  document.getElementById("categoryFilter").addEventListener("change", (e) => {
    currentFilterCategory = e.target.value;
    loadAllDashboardData();
  });

  document.getElementById("customerSearch").addEventListener("input", (e) => {
    currentPage = 1;
    loadCustomersTable();
  });

  document.getElementById("rfmFilterSelect").addEventListener("change", (e) => {
    currentPage = 1;
    loadCustomersTable();
  });
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
    console.error("Failed to load filter options", err);
  }
}

async function loadAllDashboardData() {
  await Promise.all([
    loadKPIs(),
    loadMonthlyTrend(),
    loadTopProducts(),
    loadCategories(),
    loadCountries(),
    loadRFM(),
    loadCustomersTable()
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

    const ctx = document.getElementById("monthlyChart").getContext("2d");

    if (monthlyChart) monthlyChart.destroy();

    monthlyChart = new Chart(ctx, {
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
            label: "Order Count",
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
        interaction: { mode: "index", intersect: false },
        scales: {
          y: {
            type: "linear",
            position: "left",
            ticks: {
              callback: (val) => `£${(val / 1000).toFixed(0)}k`
            },
            grid: { color: "#f1f5f9" }
          },
          y1: {
            type: "linear",
            position: "right",
            grid: { drawOnChartArea: false }
          },
          x: { grid: { display: false } }
        }
      }
    });
  } catch (err) {
    console.error("Error loading monthly trend", err);
  }
}

async function loadTopProducts() {
  try {
    const url = `/api/top-products?limit=10&category=${encodeURIComponent(currentFilterCategory)}`;
    const res = await fetch(url);
    const data = await res.json();

    const labels = data.map((d) => d.description.length > 22 ? d.description.slice(0, 22) + "..." : d.description);
    const revenues = data.map((d) => d.total_revenue);

    const ctx = document.getElementById("topProductsChart").getContext("2d");

    if (topProductsChart) topProductsChart.destroy();

    topProductsChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Gross Revenue (£)",
            data: revenues,
            backgroundColor: "#0ea5e9",
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Revenue: £${ctx.raw.toLocaleString("en-GB")}`
            }
          }
        },
        scales: {
          x: {
            ticks: { callback: (val) => `£${(val / 1000).toFixed(0)}k` },
            grid: { color: "#f1f5f9" }
          },
          y: { grid: { display: false } }
        }
      }
    });
  } catch (err) {
    console.error("Error loading top products", err);
  }
}

async function loadCategories() {
  try {
    const res = await fetch("/api/categories");
    const data = await res.json();

    const labels = data.map((d) => d.category);
    const revenues = data.map((d) => d.revenue);

    const ctx = document.getElementById("categoryChart").getContext("2d");

    if (categoryChart) categoryChart.destroy();

    categoryChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: revenues,
            backgroundColor: [
              "#2563eb", "#0ea5e9", "#10b981", "#f59e0b",
              "#8b5cf6", "#ec4899", "#64748b", "#14b8a6"
            ],
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right" },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: £${ctx.raw.toLocaleString("en-GB")} (${data[ctx.dataIndex].share_pct}%)`
            }
          }
        }
      }
    });
  } catch (err) {
    console.error("Error loading categories", err);
  }
}

async function loadCountries() {
  try {
    const res = await fetch("/api/countries?limit=6");
    const data = await res.json();

    const labels = data.map((d) => d.country);
    const revenues = data.map((d) => d.revenue);

    const ctx = document.getElementById("countryChart").getContext("2d");

    if (countryChart) countryChart.destroy();

    countryChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Revenue (£)",
            data: revenues,
            backgroundColor: "#10b981",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Revenue: £${ctx.raw.toLocaleString("en-GB")} (${data[ctx.dataIndex].share_pct}%)`
            }
          }
        },
        scales: {
          y: {
            ticks: { callback: (val) => `£${(val / 1000).toFixed(0)}k` },
            grid: { color: "#f1f5f9" }
          },
          x: { grid: { display: false } }
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

    const segs = data.segments;
    const labels = segs.map((s) => s.Customer_Segment);
    const revs = segs.map((s) => s.Total_Revenue);

    const ctx = document.getElementById("rfmChart").getContext("2d");

    if (rfmChart) rfmChart.destroy();

    rfmChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Segment Revenue (£)",
            data: revs,
            backgroundColor: "#8b5cf6",
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Revenue: £${ctx.raw.toLocaleString("en-GB")} (${segs[ctx.dataIndex].Rev_Share_Pct}%)`
            }
          }
        },
        scales: {
          x: {
            ticks: { callback: (val) => `£${(val / 1000).toFixed(0)}k` },
            grid: { color: "#f1f5f9" }
          },
          y: { grid: { display: false } }
        }
      }
    });
  } catch (err) {
    console.error("Error loading RFM segments", err);
  }
}

async function loadCustomersTable() {
  try {
    const searchVal = document.getElementById("customerSearch").value;
    const segVal = document.getElementById("rfmFilterSelect").value;

    const url = `/api/customers?segment=${encodeURIComponent(segVal)}&search=${encodeURIComponent(searchVal)}&page=${currentPage}&page_size=15`;
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
  currentPage += delta;
  loadCustomersTable();
}

function exportCurrentCustomers() {
  window.open("/api/customers?page=1&page_size=1000", "_blank");
}
