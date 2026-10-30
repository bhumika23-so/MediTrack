/**
 * charts.js - Chart.js Visualizations for MediTrack Dashboard
 */

const MediTrackCharts = (function () {
    let categoryChartInstance = null;
    let stockComparisonChartInstance = null;
    let expiryHealthChartInstance = null;

    // Healthcare color palettes
    const palette = {
        primary: "#2563eb",
        teal: "#0284c7",
        cyan: "#06b6d4",
        emerald: "#10b981",
        amber: "#f59e0b",
        red: "#ef4444",
        purple: "#8b5cf6",
        indigo: "#6366f1",
        slate: "#64748b"
    };

    const categoryColors = [
        "#2563eb", "#0284c7", "#0d9488", "#10b981",
        "#8b5cf6", "#f59e0b", "#ec4899", "#6366f1",
        "#14b8a6", "#3b82f6", "#f97316", "#64748b"
    ];

    function initCategoryChart(labels, data) {
        const ctx = document.getElementById("categoryChart");
        if (!ctx || typeof Chart === "undefined") return;

        if (categoryChartInstance) {
            categoryChartInstance.destroy();
        }

        categoryChartInstance = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels.length ? labels : ["No Data"],
                datasets: [{
                    data: data.length ? data : [1],
                    backgroundColor: categoryColors.slice(0, Math.max(labels.length, 1)),
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "right",
                        labels: {
                            boxWidth: 12,
                            padding: 10,
                            font: { size: 11, family: "'Inter', sans-serif" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` ${context.label}: ${context.raw} usable units`;
                            }
                        }
                    }
                },
                cutout: "68%"
            }
        });
    }

    function initStockComparisonChart(labels, usableData, minData) {
        const ctx = document.getElementById("stockComparisonChart");
        if (!ctx || typeof Chart === "undefined") return;

        if (stockComparisonChartInstance) {
            stockComparisonChartInstance.destroy();
        }

        // Truncate long medicine names for chart labels
        const cleanLabels = labels.map(l => l.length > 14 ? l.substring(0, 12) + "..." : l);

        stockComparisonChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: cleanLabels,
                datasets: [
                    {
                        label: "Usable Stock",
                        data: usableData,
                        backgroundColor: "#2563eb",
                        borderRadius: 4,
                        barPercentage: 0.6
                    },
                    {
                        label: "Min Stock Threshold",
                        data: minData,
                        backgroundColor: "#cbd5e1",
                        borderRadius: 4,
                        barPercentage: 0.6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        labels: {
                            boxWidth: 12,
                            font: { size: 11, family: "'Inter', sans-serif" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title: function(items) {
                                const idx = items[0].dataIndex;
                                return labels[idx];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#f1f5f9" },
                        ticks: { font: { size: 10 } }
                    }
                }
            }
        });
    }

    function initExpiryHealthChart(labels, data) {
        const ctx = document.getElementById("expiryHealthChart");
        if (!ctx || typeof Chart === "undefined") return;

        if (expiryHealthChartInstance) {
            expiryHealthChartInstance.destroy();
        }

        expiryHealthChartInstance = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        palette.emerald,  // Safe
                        palette.amber,    // Expiring Soon
                        palette.red       // Expired
                    ],
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            boxWidth: 12,
                            padding: 10,
                            font: { size: 11, family: "'Inter', sans-serif" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` ${context.label}: ${context.raw} batches`;
                            }
                        }
                    }
                },
                cutout: "62%"
            }
        });
    }

    function updateAll(chartData) {
        if (!chartData) return;
        if (chartData.categories) {
            initCategoryChart(chartData.categories.labels, chartData.categories.data);
        }
        if (chartData.stock_comparison) {
            initStockComparisonChart(
                chartData.stock_comparison.labels,
                chartData.stock_comparison.usable,
                chartData.stock_comparison.minimum
            );
        }
        if (chartData.expiry_breakdown) {
            initExpiryHealthChart(chartData.expiry_breakdown.labels, chartData.expiry_breakdown.data);
        }
    }

    return {
        updateAll: updateAll
    };
})();
