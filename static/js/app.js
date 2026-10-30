/**
 * app.js - MediTrack Core Application Controller
 * Handles routing, API communications, UI state, modals, and tables.
 */

// Application State
const State = {
    currentView: "dashboard",
    medicines: [],
    batches: [],
    predictions: [],
    consumptionLogs: [],
    summary: null
};

// ========================================================
// INITIALIZATION
// ========================================================
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initModals();
    initSearchAndFilters();
    initFormHandlers();
    initQuickActions();

    // Set today's date in sidebar & topbar
    const todayStr = new Date().toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric"
    });
    const dateEl = document.getElementById("currentDateDisplay");
    if (dateEl) dateEl.textContent = todayStr;

    // Set today as default in date fields
    const todayIso = new Date().toISOString().split("T")[0];
    const batchRecInput = document.getElementById("batchFormReceived");
    if (batchRecInput) batchRecInput.value = todayIso;
    const dispDateInput = document.getElementById("dispenseDate");
    if (dispDateInput) dispDateInput.value = todayIso;

    // Load initial data
    loadAllData();
});

// ========================================================
// NAVIGATION & ROUTING
// ========================================================
function initNavigation() {
    const navLinks = document.querySelectorAll(".sidebar-nav .nav-item");
    const views = document.querySelectorAll(".content-view");
    const mobileBtn = document.getElementById("mobileMenuBtn");
    const sidebar = document.getElementById("sidebar");

    function setView(viewId) {
        State.currentView = viewId;

        // Toggle active nav class
        navLinks.forEach(link => {
            if (link.dataset.view === viewId) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        });

        // Toggle active view section
        views.forEach(v => {
            if (v.id === `view-${viewId}`) {
                v.classList.add("active");
            } else {
                v.classList.remove("active");
            }
        });

        // Update topbar headers
        updateHeaderTitles(viewId);

        // Refresh relevant view data
        refreshCurrentView(viewId);

        // Close sidebar on mobile
        if (sidebar && sidebar.classList.contains("open")) {
            sidebar.classList.remove("open");
        }
    }

    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const viewId = link.dataset.view;
            window.location.hash = viewId;
            setView(viewId);
        });
    });

    // Handle hash change or direct load
    window.addEventListener("hashchange", () => {
        const hash = window.location.hash.replace("#", "");
        if (hash) setView(hash);
    });

    if (window.location.hash) {
        const hash = window.location.hash.replace("#", "");
        setView(hash);
    }

    // Mobile sidebar toggle
    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }
}

function updateHeaderTitles(viewId) {
    const titleEl = document.getElementById("pageTitle");
    const subEl = document.getElementById("pageSubtitle");
    if (!titleEl || !subEl) return;

    const titles = {
        "dashboard": { title: "Dashboard Overview", sub: "Real-time inventory levels, safety alerts & analytics" },
        "medicines": { title: "Medicine Inventory", sub: "Catalogue of medicines, categories, and stock limits" },
        "batches": { title: "Batch & Stock Tracking", sub: "Batch-wise quantities, expiry monitoring & storage details" },
        "expiry-alerts": { title: "Expiry Safety Alerts", sub: "Batches expiring within 30 days & quarantined expired units" },
        "low-stock": { title: "Low Stock Alerts", sub: "Medicines below minimum threshold & stockout warnings" },
        "predictions": { title: "Stock Shortage Prediction", sub: "Consumption velocity modeling & runout date forecasting" },
        "consumption": { title: "Dispense & Usage History", sub: "Audited log of outpatient & clinical medicine dispensing" }
    };

    const conf = titles[viewId] || titles["dashboard"];
    titleEl.textContent = conf.title;
    subEl.textContent = conf.sub;
}

window.navigateView = function(viewId) {
    window.location.hash = viewId;
    const navLink = document.querySelector(`.sidebar-nav .nav-item[data-view="${viewId}"]`);
    if (navLink) navLink.click();
};

function refreshCurrentView(viewId) {
    switch (viewId) {
        case "dashboard":
            loadDashboard();
            break;
        case "medicines":
            loadMedicines();
            break;
        case "batches":
            loadBatches();
            break;
        case "expiry-alerts":
            loadExpiryAlerts();
            break;
        case "low-stock":
            loadLowStockAlerts();
            break;
        case "predictions":
            loadPredictions();
            break;
        case "consumption":
            loadConsumptionLogs();
            break;
    }
}

function loadAllData() {
    loadDashboard();
    loadMedicines();
}

// ========================================================
// TOAST NOTIFICATION SYSTEM
// ========================================================
function showToast(type, title, message, duration = 4000) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "fa-circle-check";
    if (type === "danger") icon = "fa-circle-exclamation";
    if (type === "warning") icon = "fa-triangle-exclamation";
    if (type === "info") icon = "fa-circle-info";

    toast.innerHTML = `
        <i class="fa-solid ${icon} toast-icon"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close">&times;</button>
    `;

    container.appendChild(toast);

    const closeBtn = toast.querySelector(".toast-close");
    closeBtn.addEventListener("click", () => {
        toast.remove();
    });

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            setTimeout(() => toast.remove(), 250);
        }
    }, duration);
}

// ========================================================
// MODAL CONTROLLERS
// ========================================================
function initModals() {
    // Close button triggers
    document.querySelectorAll("[data-modal]").forEach(btn => {
        btn.addEventListener("click", () => {
            const modalId = btn.getAttribute("data-modal");
            closeModal(modalId);
        });
    });

    // Close on backdrop click
    document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
        backdrop.addEventListener("click", (e) => {
            if (e.target === backdrop) {
                closeModal(backdrop.id);
            }
        });
    });

    // Close on ESC
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal-backdrop.open").forEach(m => closeModal(m.id));
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("open");
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove("open");
    }
}

// ========================================================
// QUICK ACTION BUTTONS
// ========================================================
function initQuickActions() {
    // Add Medicine Button (topbar & view button)
    const btnAddMedQuick = document.getElementById("btnAddMedicineQuick");
    const btnAddMedModal = document.getElementById("btnAddMedicineModalOpen");
    const openAddMed = () => {
        document.getElementById("medicineForm").reset();
        document.getElementById("medFormId").value = "";
        document.getElementById("medicineModalTitle").innerHTML = '<i class="fa-solid fa-pills"></i> Add New Medicine';
        openModal("medicineModal");
    };
    if (btnAddMedQuick) btnAddMedQuick.addEventListener("click", openAddMed);
    if (btnAddMedModal) btnAddMedModal.addEventListener("click", openAddMed);

    // Add Batch Button (topbar & view button)
    const btnAddBatchQuick = document.getElementById("btnAddBatchQuick");
    const btnAddBatchModal = document.getElementById("btnAddBatchModalOpen");
    const openAddBatch = (preselectedMedId = null) => {
        document.getElementById("batchForm").reset();
        document.getElementById("batchFormId").value = "";
        document.getElementById("batchModalTitle").innerHTML = '<i class="fa-solid fa-boxes-stacked"></i> Add Medicine Batch';
        populateMedicineSelect("batchFormMedId", preselectedMedId);
        const todayIso = new Date().toISOString().split("T")[0];
        document.getElementById("batchFormReceived").value = todayIso;
        openModal("batchModal");
    };
    if (btnAddBatchQuick) btnAddBatchQuick.addEventListener("click", () => openAddBatch());
    if (btnAddBatchModal) btnAddBatchModal.addEventListener("click", () => openAddBatch());

    // Dispense Quick Button
    const btnDispenseQuick = document.getElementById("btnDispenseQuick");
    const btnDispenseModal = document.getElementById("btnDispenseModalOpen");
    const openDispense = (preselectedMedId = null) => {
        document.getElementById("dispenseForm").reset();
        populateMedicineSelect("dispenseMedId", preselectedMedId);
        const todayIso = new Date().toISOString().split("T")[0];
        document.getElementById("dispenseDate").value = todayIso;
        const stockPrev = document.getElementById("dispenseStockInfo");
        if (stockPrev) stockPrev.style.display = "none";
        if (preselectedMedId) {
            updateDispenseBatchOptions(preselectedMedId);
        }
        openModal("dispenseModal");
    };
    if (btnDispenseQuick) btnDispenseQuick.addEventListener("click", () => openDispense());
    if (btnDispenseModal) btnDispenseModal.addEventListener("click", () => openDispense());

    // Reset Sample Data Button
    const btnReset = document.getElementById("btnResetSampleData");
    if (btnReset) {
        btnReset.addEventListener("click", () => {
            if (confirm("Reset inventory to realistic initial clinic sample data? Any manual additions will be replaced.")) {
                resetSampleData();
            }
        });
    }

    // Modal Add Batch button inside details modal
    const btnDetailAddBatch = document.getElementById("btnQuickAddBatchForMed");
    if (btnDetailAddBatch) {
        btnDetailAddBatch.addEventListener("click", () => {
            const medId = btnDetailAddBatch.getAttribute("data-med-id");
            closeModal("medDetailsModal");
            openAddBatch(medId);
        });
    }
}

function populateMedicineSelect(selectElementId, selectedId = null) {
    const sel = document.getElementById(selectElementId);
    if (!sel) return;

    sel.innerHTML = '<option value="">Select Medicine...</option>';
    State.medicines.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = `${m.name} (${m.category}) - ${m.usable_stock} ${m.unit} in stock`;
        if (selectedId && String(m.id) === String(selectedId)) {
            opt.selected = true;
        }
        sel.appendChild(opt);
    });
}

function updateDispenseBatchOptions(medicineId) {
    const batchSelect = document.getElementById("dispenseBatchId");
    const stockPrev = document.getElementById("dispenseStockInfo");
    const availVal = document.getElementById("dispenseAvailableVal");
    if (!batchSelect) return;

    batchSelect.innerHTML = '<option value="">Auto FEFO (Earliest Expiring Non-Expired)</option>';

    const med = State.medicines.find(m => String(m.id) === String(medicineId));
    if (med && stockPrev && availVal) {
        stockPrev.style.display = "flex";
        availVal.textContent = `${med.usable_stock} ${med.unit} available`;
    }

    fetch(`/api/batches?medicine_id=${medicineId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Filter only non-expired batches with positive quantity
                const usableBatches = data.batches.filter(b => b.is_usable && b.quantity > 0);
                usableBatches.forEach(b => {
                    const opt = document.createElement("option");
                    opt.value = b.id;
                    opt.textContent = `Batch ${b.batch_number} (Qty: ${b.quantity}, Exp: ${b.expiry_date} - ${b.label})`;
                    batchSelect.appendChild(opt);
                });
            }
        })
        .catch(err => console.error("Error loading batches for dispense:", err));
}

// When medicine is selected in dispense modal, update batch options and stock info
document.addEventListener("change", (e) => {
    if (e.target && e.target.id === "dispenseMedId") {
        const medId = e.target.value;
        if (medId) {
            updateDispenseBatchOptions(medId);
        } else {
            const stockPrev = document.getElementById("dispenseStockInfo");
            if (stockPrev) stockPrev.style.display = "none";
        }
    }
});

// ========================================================
// API DATA LOADERS
// ========================================================

/** 1. DASHBOARD OVERVIEW */
function loadDashboard() {
    fetch("/api/analytics/summary")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            State.summary = data;
            const k = data.kpis;

            // Update KPI elements
            const setTxt = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };

            setTxt("kpiTotalMedicines", k.total_medicines);
            setTxt("kpiUsableStock", k.total_usable_stock.toLocaleString());
            setTxt("kpiExpiringSoon", k.expiring_soon_count);
            setTxt("kpiExpiredBatches", k.expired_batch_count);
            setTxt("kpiExpiredUnits", `${k.total_expired_stock} units non-usable`);
            setTxt("kpiLowStock", k.low_stock_count);
            setTxt("kpiOutOfStockCount", `${k.out_of_stock_count} out of stock`);
            setTxt("kpiCriticalShortages", k.critical_shortage_count);

            // Update sidebar notification badges
            setTxt("navExpiringCount", k.expiring_soon_count);
            setTxt("navLowStockCount", k.low_stock_count);

            // Update Charts
            if (window.MediTrackCharts) {
                MediTrackCharts.updateAll(data.charts);
            }
        })
        .catch(err => console.error("Error loading dashboard summary:", err));

    // Load urgent preview tables on dashboard
    loadDashboardPreviewTables();
}

function loadDashboardPreviewTables() {
    // Urgent Expiry Table Preview
    fetch("/api/alerts/expiry")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            const tbody = document.querySelector("#dashboardExpiryTable tbody");
            if (!tbody) return;

            if (data.expiring_soon.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No medicines expiring in the next 30 days. All batches safe!</td></tr>';
                return;
            }

            tbody.innerHTML = data.expiring_soon.slice(0, 5).map(b => `
                <tr>
                    <td><strong>${escapeHtml(b.medicine_name)}</strong></td>
                    <td><span class="batch-tag">${escapeHtml(b.batch_number)}</span></td>
                    <td>${b.quantity} ${escapeHtml(b.unit || 'units')}</td>
                    <td>${b.expiry_date}</td>
                    <td><span class="badge ${b.badge_class}"><i class="fa-solid fa-clock"></i> ${b.label}</span></td>
                </tr>
            `).join("");
        });

    // Low Stock Table Preview
    fetch("/api/alerts/low-stock")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            const tbody = document.querySelector("#dashboardLowStockTable tbody");
            if (!tbody) return;

            const items = [...data.out_of_stock, ...data.low_stock];
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">All medicines are above minimum stock levels.</td></tr>';
                return;
            }

            tbody.innerHTML = items.slice(0, 5).map(m => `
                <tr>
                    <td><strong>${escapeHtml(m.name)}</strong></td>
                    <td><span class="${m.usable_stock === 0 ? 'text-danger' : 'text-warning'} font-weight-bold">${m.usable_stock} ${m.unit}</span></td>
                    <td>${m.min_stock} ${m.unit}</td>
                    <td><span class="badge badge-danger">-${m.deficit}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="openAddBatchModalForMed(${m.id})">
                            <i class="fa-solid fa-plus"></i> Restock
                        </button>
                    </td>
                </tr>
            `).join("");
        });
}

/** 2. MEDICINES VIEW */
function loadMedicines() {
    fetch("/api/medicines")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            State.medicines = data.medicines;

            const counter = document.getElementById("navMedCount");
            if (counter) counter.textContent = State.medicines.length;

            populateCategoryFilter(State.medicines);
            renderMedicinesTable(State.medicines);
        })
        .catch(err => console.error("Error loading medicines:", err));
}

function populateCategoryFilter(medicines) {
    const sel = document.getElementById("categoryFilter");
    if (!sel) return;

    const currentVal = sel.value;
    const categories = Array.from(new Set(medicines.map(m => m.category).filter(Boolean))).sort();

    sel.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
        const opt = document.createElement("option");
        opt.value = cat;
        opt.textContent = cat;
        if (cat === currentVal) opt.selected = true;
        sel.appendChild(opt);
    });
}

function renderMedicinesTable(medicines) {
    const tbody = document.querySelector("#medicinesTable tbody");
    if (!tbody) return;

    if (medicines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No medicines found matching criteria.</td></tr>';
        return;
    }

    tbody.innerHTML = medicines.map(m => {
        // Build badges summary for expired / expiring batches
        let warningsHtml = "";
        if (m.has_expired) {
            warningsHtml += `<span class="badge badge-danger ml-1" title="${m.expired_stock} expired units quarantined"><i class="fa-solid fa-ban"></i> ${m.expired_stock} Expired</span> `;
        }
        if (m.has_expiring_soon) {
            warningsHtml += `<span class="badge badge-warning ml-1" title="Has batches expiring soon"><i class="fa-solid fa-clock"></i> Expiring Soon</span>`;
        }

        return `
            <tr>
                <td>
                    <div style="font-weight: 600; color: #0f172a;">${escapeHtml(m.name)}</div>
                    ${m.description ? `<small class="text-muted">${escapeHtml(m.description)}</small>` : ""}
                </td>
                <td><span class="badge badge-gray">${escapeHtml(m.category)}</span></td>
                <td>${escapeHtml(m.unit)}</td>
                <td>
                    <strong class="${m.usable_stock === 0 ? 'text-danger' : (m.usable_stock < m.min_stock ? 'text-warning' : 'text-success')}">
                        ${m.usable_stock}
                    </strong>
                    ${warningsHtml}
                </td>
                <td>${m.min_stock}</td>
                <td><span class="badge ${m.stock_badge}">${escapeHtml(m.stock_label)}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="viewMedicineDetails(${m.id})">
                        <i class="fa-solid fa-layer-group"></i> ${m.batch_count} Batch${m.batch_count === 1 ? '' : 'es'}
                    </button>
                </td>
                <td>
                    <div class="action-btns-group">
                        <button class="btn btn-sm btn-outline" title="Add Batch" onclick="openAddBatchModalForMed(${m.id})">
                            <i class="fa-solid fa-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" title="Dispense" onclick="openDispenseForMed(${m.id})">
                            <i class="fa-solid fa-hand-holding-medical"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" title="Edit Medicine" onclick="editMedicine(${m.id})">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-sm btn-outline text-danger" title="Delete Medicine" onclick="deleteMedicine(${m.id}, '${escapeHtml(m.name)}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

/** 3. BATCHES VIEW */
function loadBatches() {
    fetch("/api/batches")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            State.batches = data.batches;
            renderBatchesTable(State.batches);
        })
        .catch(err => console.error("Error loading batches:", err));
}

function renderBatchesTable(batches) {
    const tbody = document.querySelector("#batchesTable tbody");
    if (!tbody) return;

    if (batches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No batches found.</td></tr>';
        return;
    }

    tbody.innerHTML = batches.map(b => `
        <tr>
            <td><strong class="batch-tag">${escapeHtml(b.batch_number)}</strong></td>
            <td>
                <div style="font-weight: 600;">${escapeHtml(b.medicine_name)}</div>
                <small class="text-muted">${escapeHtml(b.category)}</small>
            </td>
            <td>
                <strong class="${b.quantity === 0 ? 'text-muted' : (b.is_usable ? 'text-success' : 'text-danger')}">
                    ${b.quantity}
                </strong> / ${b.initial_quantity} ${escapeHtml(b.unit)}
            </td>
            <td>${b.expiry_date}</td>
            <td>
                <span class="badge ${b.badge_class}">
                    ${b.label}
                </span>
            </td>
            <td>
                ${b.status === 'EXPIRED' ? '<span class="badge badge-danger">Expired (Quarantine)</span>' :
                  b.status === 'EXPIRING_SOON' ? '<span class="badge badge-warning">Expiring Soon</span>' :
                  '<span class="badge badge-success">Good / Usable</span>'}
            </td>
            <td>${escapeHtml(b.supplier || 'N/A')}</td>
            <td>
                <div class="action-btns-group">
                    ${b.status === 'EXPIRED' && b.quantity > 0 ? `
                        <button class="btn btn-sm btn-danger" title="Quarantine / Dispose" onclick="quarantineBatch(${b.id}, '${escapeHtml(b.batch_number)}')">
                            <i class="fa-solid fa-ban"></i> Quarantine
                        </button>
                    ` : ""}
                    <button class="btn btn-sm btn-outline" title="Edit Batch" onclick="editBatch(${b.id})">
                        <i class="fa-solid fa-pen"></i>
                    </button>
                    <button class="btn btn-sm btn-outline text-danger" title="Delete Batch" onclick="deleteBatch(${b.id}, '${escapeHtml(b.batch_number)}')">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join("");
}

/** 4. EXPIRY ALERTS VIEW */
function loadExpiryAlerts() {
    fetch("/api/alerts/expiry")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            const sum = data.summary;

            document.getElementById("alertExpiringCount").textContent = sum.expiring_soon_count;
            document.getElementById("alertExpiredCount").textContent = sum.expired_count;
            document.getElementById("expiringSoonTableBadge").textContent = `${sum.expiring_soon_count} Batches`;
            document.getElementById("expiredTableBadge").textContent = `${sum.expired_count} Batches (${sum.wasted_units} Units)`;

            // Render Expiring Soon Table
            const soonTbody = document.querySelector("#expiringSoonTable tbody");
            if (soonTbody) {
                if (data.expiring_soon.length === 0) {
                    soonTbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No medicines expiring within the next 30 days! Safe inventory.</td></tr>';
                } else {
                    soonTbody.innerHTML = data.expiring_soon.map(b => `
                        <tr>
                            <td><strong>${escapeHtml(b.medicine_name)}</strong></td>
                            <td><span class="batch-tag">${escapeHtml(b.batch_number)}</span></td>
                            <td><strong class="text-warning">${b.quantity}</strong> ${escapeHtml(b.unit)}</td>
                            <td>${b.expiry_date}</td>
                            <td><span class="badge badge-warning"><i class="fa-solid fa-hourglass-half"></i> ${b.label}</span></td>
                            <td><span class="badge badge-warning">Priority Dispense</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="openDispenseForMed(${b.medicine_id}, ${b.id})">
                                    <i class="fa-solid fa-hand-holding-medical"></i> Dispense Now
                                </button>
                            </td>
                        </tr>
                    `).join("");
                }
            }

            // Render Expired Table (Displayed separately as required)
            const expTbody = document.querySelector("#expiredTable tbody");
            if (expTbody) {
                if (data.expired.length === 0) {
                    expTbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Zero expired batches in inventory. Excellent compliance!</td></tr>';
                } else {
                    expTbody.innerHTML = data.expired.map(b => `
                        <tr style="background-color: #fffaf0;">
                            <td><strong class="text-danger">${escapeHtml(b.medicine_name)}</strong></td>
                            <td><span class="batch-tag" style="border-color: #fca5a5;">${escapeHtml(b.batch_number)}</span></td>
                            <td><strong class="text-danger">${b.quantity}</strong> ${escapeHtml(b.unit)}</td>
                            <td>${b.expiry_date}</td>
                            <td><span class="badge badge-danger"><i class="fa-solid fa-ban"></i> Expired ${b.abs_days} days ago</span></td>
                            <td>${escapeHtml(b.supplier || 'N/A')}</td>
                            <td>
                                <button class="btn btn-sm btn-danger" onclick="quarantineBatch(${b.id}, '${escapeHtml(b.batch_number)}')">
                                    <i class="fa-solid fa-shield-virus"></i> Quarantine / Dispose
                                </button>
                            </td>
                        </tr>
                    `).join("");
                }
            }
        })
        .catch(err => console.error("Error loading expiry alerts:", err));
}

/** 5. LOW STOCK ALERTS VIEW */
function loadLowStockAlerts() {
    fetch("/api/alerts/low-stock")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            const sum = data.summary;

            document.getElementById("outOfStockBannerCount").textContent = sum.out_of_stock_count;
            document.getElementById("lowStockBannerCount").textContent = sum.low_stock_count;
            document.getElementById("outOfStockTableBadge").textContent = `${sum.out_of_stock_count} Items`;
            document.getElementById("lowStockTableBadge").textContent = `${sum.low_stock_count} Items`;

            // 1. Out of Stock Table
            const outTbody = document.querySelector("#outOfStockTable tbody");
            if (outTbody) {
                if (data.out_of_stock.length === 0) {
                    outTbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No medicines currently out of stock.</td></tr>';
                } else {
                    outTbody.innerHTML = data.out_of_stock.map(m => `
                        <tr style="background-color: #fef2f2;">
                            <td><strong>${escapeHtml(m.name)}</strong></td>
                            <td><span class="badge badge-gray">${escapeHtml(m.category)}</span></td>
                            <td><span class="badge badge-danger">0 ${escapeHtml(m.unit)}</span></td>
                            <td>${m.min_stock} ${escapeHtml(m.unit)}</td>
                            <td><strong class="text-danger">+${m.deficit} needed</strong></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="openAddBatchModalForMed(${m.id})">
                                    <i class="fa-solid fa-plus"></i> Restock Batch
                                </button>
                            </td>
                        </tr>
                    `).join("");
                }
            }

            // 2. Low Stock Table
            const lowTbody = document.querySelector("#lowStockTable tbody");
            if (lowTbody) {
                if (data.low_stock.length === 0) {
                    lowTbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">All active medicines meet or exceed minimum stock levels.</td></tr>';
                } else {
                    lowTbody.innerHTML = data.low_stock.map(m => {
                        const pct = Math.min(100, m.stock_percentage || 0);
                        return `
                            <tr>
                                <td><strong>${escapeHtml(m.name)}</strong></td>
                                <td><span class="badge badge-gray">${escapeHtml(m.category)}</span></td>
                                <td><strong class="text-warning">${m.usable_stock}</strong> ${escapeHtml(m.unit)}</td>
                                <td>${m.min_stock} ${escapeHtml(m.unit)}</td>
                                <td style="width: 140px;">
                                    <div style="font-size: 0.76rem; font-weight: 600; color: #64748b; margin-bottom: 2px;">${pct}%</div>
                                    <div class="progress-bar-container">
                                        <div class="progress-fill warning" style="width: ${pct}%"></div>
                                    </div>
                                </td>
                                <td><span class="badge badge-warning">+${m.deficit} needed</span></td>
                                <td>
                                    <button class="btn btn-sm btn-outline" onclick="openAddBatchModalForMed(${m.id})">
                                        <i class="fa-solid fa-plus"></i> Add Batch
                                    </button>
                                </td>
                            </tr>
                        `;
                    }).join("");
                }
            }
        })
        .catch(err => console.error("Error loading low stock alerts:", err));
}

/** 6. SHORTAGE PREDICTION VIEW */
function loadPredictions() {
    fetch("/api/analytics/predictions")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            State.predictions = data.predictions;

            document.getElementById("predCriticalCount").textContent = data.summary.critical_shortages;
            document.getElementById("predModerateCount").textContent = data.summary.moderate_shortages;

            const tbody = document.querySelector("#predictionsTable tbody");
            if (!tbody) return;

            if (data.predictions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No prediction data available.</td></tr>';
                return;
            }

            tbody.innerHTML = data.predictions.map(p => {
                let daysDisplay = "";
                if (p.days_remaining === null) {
                    daysDisplay = '<span class="text-muted">No usage</span>';
                } else if (p.days_remaining === 0) {
                    daysDisplay = '<strong class="text-danger">0 Days (Empty)</strong>';
                } else if (p.days_remaining <= 7) {
                    daysDisplay = `<strong class="text-danger">${p.days_remaining} Days</strong>`;
                } else if (p.days_remaining <= 15) {
                    daysDisplay = `<strong class="text-warning">${p.days_remaining} Days</strong>`;
                } else {
                    daysDisplay = `<strong class="text-success">${p.days_remaining} Days</strong>`;
                }

                return `
                    <tr>
                        <td>
                            <strong>${escapeHtml(p.name)}</strong>
                            <div class="text-muted" style="font-size: 0.75rem;">${escapeHtml(p.category)}</div>
                        </td>
                        <td><strong>${p.usable_stock}</strong> ${escapeHtml(p.unit)}</td>
                        <td>${p.consumption_30d} ${escapeHtml(p.unit)}</td>
                        <td><strong>${p.avg_daily_usage}</strong> / day</td>
                        <td>${daysDisplay}</td>
                        <td><span class="badge ${p.risk_badge}">${p.risk_label}</span></td>
                        <td>
                            ${p.reorder_qty > 0 ? `<strong class="text-primary">+${p.reorder_qty} ${escapeHtml(p.unit)}</strong>` : '<span class="text-muted">Stock Sufficient</span>'}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline" onclick="openAddBatchModalForMed(${p.medicine_id})">
                                <i class="fa-solid fa-plus"></i> Reorder
                            </button>
                        </td>
                    </tr>
                `;
            }).join("");
        })
        .catch(err => console.error("Error loading predictions:", err));
}

/** 7. CONSUMPTION & DISPENSE AUDIT LOGS */
function loadConsumptionLogs() {
    fetch("/api/consumption?limit=50")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            State.consumptionLogs = data.logs;

            const tbody = document.querySelector("#consumptionTable tbody");
            if (!tbody) return;

            if (data.logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No dispense logs recorded yet.</td></tr>';
                return;
            }

            tbody.innerHTML = data.logs.map(log => `
                <tr>
                    <td>#${log.id}</td>
                    <td>${log.dispensed_date}</td>
                    <td><strong>${escapeHtml(log.medicine_name)}</strong></td>
                    <td><span class="batch-tag">${escapeHtml(log.batch_number || 'Auto FEFO')}</span></td>
                    <td><strong class="text-primary">${log.quantity} ${escapeHtml(log.unit || '')}</strong></td>
                    <td>${escapeHtml(log.dispensed_to || 'N/A')}</td>
                </tr>
            `).join("");
        })
        .catch(err => console.error("Error loading consumption logs:", err));
}

// ========================================================
// SEARCH & FILTER HANDLERS
// ========================================================
function initSearchAndFilters() {
    // Global Topbar Search
    const globalSearch = document.getElementById("globalSearchInput");
    if (globalSearch) {
        globalSearch.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            if (query.length > 0 && State.currentView !== "medicines") {
                navigateView("medicines");
            }
            const medSearch = document.getElementById("medicineSearchInput");
            if (medSearch) {
                medSearch.value = query;
                filterMedicines();
            }
        });
    }

    // Medicine View Search & Filters
    const medSearch = document.getElementById("medicineSearchInput");
    const catFilter = document.getElementById("categoryFilter");
    const statusFilter = document.getElementById("stockStatusFilter");

    if (medSearch) medSearch.addEventListener("input", filterMedicines);
    if (catFilter) catFilter.addEventListener("change", filterMedicines);
    if (statusFilter) statusFilter.addEventListener("change", filterMedicines);

    // Batch View Search & Filters
    const batchSearch = document.getElementById("batchSearchInput");
    const batchExpiryFilter = document.getElementById("batchExpiryFilter");

    if (batchSearch) batchSearch.addEventListener("input", filterBatches);
    if (batchExpiryFilter) batchExpiryFilter.addEventListener("change", filterBatches);
}

function filterMedicines() {
    const q = (document.getElementById("medicineSearchInput")?.value || "").toLowerCase().trim();
    const cat = document.getElementById("categoryFilter")?.value || "";
    const status = document.getElementById("stockStatusFilter")?.value || "";

    const filtered = State.medicines.filter(m => {
        const matchesQuery = !q || m.name.toLowerCase().includes(q) || (m.category && m.category.toLowerCase().includes(q));
        const matchesCat = !cat || m.category === cat;
        const matchesStatus = !status || m.stock_status === status;
        return matchesQuery && matchesCat && matchesStatus;
    });

    renderMedicinesTable(filtered);
}

function filterBatches() {
    const q = (document.getElementById("batchSearchInput")?.value || "").toLowerCase().trim();
    const exp = document.getElementById("batchExpiryFilter")?.value || "";

    const filtered = State.batches.filter(b => {
        const matchesQuery = !q || 
            b.batch_number.toLowerCase().includes(q) || 
            (b.medicine_name && b.medicine_name.toLowerCase().includes(q)) ||
            (b.supplier && b.supplier.toLowerCase().includes(q));
        const matchesExp = !exp || b.status === exp;
        return matchesQuery && matchesExp;
    });

    renderBatchesTable(filtered);
}

// ========================================================
// FORM SUBMISSION HANDLERS
// ========================================================
function initFormHandlers() {
    // 1. Medicine Form (Add / Edit)
    const medForm = document.getElementById("medicineForm");
    if (medForm) {
        medForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const id = document.getElementById("medFormId").value;
            const payload = {
                name: document.getElementById("medFormName").value.trim(),
                category: document.getElementById("medFormCategory").value.trim(),
                unit: document.getElementById("medFormUnit").value.trim(),
                min_stock: parseInt(document.getElementById("medFormMinStock").value, 10),
                description: document.getElementById("medFormDesc").value.trim()
            };

            const isEdit = Boolean(id);
            const url = isEdit ? `/api/medicines/${id}` : "/api/medicines";
            const method = isEdit ? "PUT" : "POST";

            fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(res => {
                if (res.success) {
                    showToast("success", "Medicine Saved", res.message || "Saved successfully.");
                    closeModal("medicineModal");
                    loadMedicines();
                    loadDashboard();
                } else {
                    showToast("danger", "Save Failed", res.error || "Unable to save medicine.");
                }
            })
            .catch(err => {
                showToast("danger", "Network Error", "Unable to reach server.");
            });
        });
    }

    // 2. Batch Form (Add / Edit)
    const batchForm = document.getElementById("batchForm");
    if (batchForm) {
        batchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const id = document.getElementById("batchFormId").value;
            const payload = {
                medicine_id: parseInt(document.getElementById("batchFormMedId").value, 10),
                batch_number: document.getElementById("batchFormNumber").value.trim().toUpperCase(),
                quantity: parseInt(document.getElementById("batchFormQuantity").value, 10),
                expiry_date: document.getElementById("batchFormExpiry").value,
                received_date: document.getElementById("batchFormReceived").value,
                supplier: document.getElementById("batchFormSupplier").value.trim(),
                unit_cost: parseFloat(document.getElementById("batchFormUnitCost").value) || 0.0,
                notes: document.getElementById("batchFormNotes").value.trim()
            };

            const isEdit = Boolean(id);
            const url = isEdit ? `/api/batches/${id}` : "/api/batches";
            const method = isEdit ? "PUT" : "POST";

            fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(res => {
                if (res.success) {
                    showToast("success", "Batch Saved", res.message || "Batch saved successfully.");
                    closeModal("batchModal");
                    loadBatches();
                    loadMedicines();
                    loadDashboard();
                    loadExpiryAlerts();
                } else {
                    showToast("danger", "Save Failed", res.error || "Unable to save batch.");
                }
            })
            .catch(err => {
                showToast("danger", "Network Error", "Unable to reach server.");
            });
        });
    }

    // 3. Dispense Form
    const dispenseForm = document.getElementById("dispenseForm");
    if (dispenseForm) {
        dispenseForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const medId = document.getElementById("dispenseMedId").value;
            const batchId = document.getElementById("dispenseBatchId").value;
            const qty = document.getElementById("dispenseQuantity").value;
            const recipient = document.getElementById("dispenseRecipient").value.trim();
            const dispDate = document.getElementById("dispenseDate").value;

            const payload = {
                medicine_id: parseInt(medId, 10),
                quantity: parseInt(qty, 10),
                batch_id: batchId ? parseInt(batchId, 10) : null,
                dispensed_to: recipient,
                dispensed_date: dispDate
            };

            fetch("/api/consumption", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(res => {
                if (res.success) {
                    showToast("success", "Dispensed Successfully", res.message);
                    closeModal("dispenseModal");
                    loadMedicines();
                    loadBatches();
                    loadDashboard();
                    loadPredictions();
                    loadConsumptionLogs();
                } else {
                    showToast("danger", "Dispense Failed", res.error || "Could not dispense medicine.");
                }
            })
            .catch(err => {
                showToast("danger", "Network Error", "Unable to complete request.");
            });
        });
    }
}

// ========================================================
// MEDICINE ACTIONS & DETAILS DRILLDOWN
// ========================================================
window.viewMedicineDetails = function(medId) {
    fetch(`/api/medicines/${medId}`)
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;
            const m = data.medicine;

            document.getElementById("medDetailsTitle").innerHTML = `<i class="fa-solid fa-file-medical"></i> ${escapeHtml(m.name)}`;
            document.getElementById("detailCategory").textContent = m.category;
            document.getElementById("detailUnit").textContent = m.unit;
            document.getElementById("detailUsable").textContent = `${m.usable_stock} ${m.unit}`;
            document.getElementById("detailExpired").textContent = `${m.expired_stock} ${m.unit}`;
            document.getElementById("detailMinStock").textContent = `${m.min_stock} ${m.unit}`;
            document.getElementById("detailDescription").textContent = m.description || "No clinical description recorded.";

            const addBatchBtn = document.getElementById("btnQuickAddBatchForMed");
            if (addBatchBtn) addBatchBtn.setAttribute("data-med-id", m.id);

            // Populate batches table in details modal
            const tbody = document.querySelector("#medDetailBatchesTable tbody");
            if (tbody) {
                if (!m.batches || m.batches.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No batches recorded for this medicine yet.</td></tr>';
                } else {
                    tbody.innerHTML = m.batches.map(b => `
                        <tr>
                            <td><span class="batch-tag">${escapeHtml(b.batch_number)}</span></td>
                            <td><strong class="${b.is_usable ? 'text-success' : 'text-danger'}">${b.quantity}</strong> / ${b.initial_quantity}</td>
                            <td>${b.expiry_date}</td>
                            <td><span class="badge ${b.badge_class}">${b.label}</span></td>
                            <td>
                                ${b.status === 'EXPIRED' ? '<span class="badge badge-danger">Expired</span>' :
                                  b.status === 'EXPIRING_SOON' ? '<span class="badge badge-warning">Expiring Soon</span>' :
                                  '<span class="badge badge-success">Good</span>'}
                            </td>
                            <td>${escapeHtml(b.supplier || 'N/A')}</td>
                            <td>
                                ${b.status === 'EXPIRED' && b.quantity > 0 ? `
                                    <button class="btn btn-sm btn-danger" onclick="quarantineBatch(${b.id}, '${escapeHtml(b.batch_number)}')">
                                        <i class="fa-solid fa-ban"></i> Quarantine
                                    </button>
                                ` : `
                                    <button class="btn btn-sm btn-outline text-danger" onclick="deleteBatch(${b.id}, '${escapeHtml(b.batch_number)}')">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                `}
                            </td>
                        </tr>
                    `).join("");
                }
            }

            openModal("medDetailsModal");
        })
        .catch(err => {
            showToast("danger", "Error", "Failed to load medicine details.");
        });
};

window.editMedicine = function(medId) {
    const med = State.medicines.find(m => m.id === medId);
    if (!med) return;

    document.getElementById("medFormId").value = med.id;
    document.getElementById("medFormName").value = med.name;
    document.getElementById("medFormCategory").value = med.category;
    document.getElementById("medFormUnit").value = med.unit;
    document.getElementById("medFormMinStock").value = med.min_stock;
    document.getElementById("medFormDesc").value = med.description || "";

    document.getElementById("medicineModalTitle").innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Edit Medicine';
    openModal("medicineModal");
};

window.deleteMedicine = function(medId, medName) {
    if (!confirm(`Are you sure you want to delete "${medName}"? This will permanently remove the medicine and all its batches.`)) {
        return;
    }

    fetch(`/api/medicines/${medId}`, { method: "DELETE" })
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                showToast("success", "Deleted", res.message);
                loadMedicines();
                loadBatches();
                loadDashboard();
            } else {
                showToast("danger", "Delete Failed", res.error || "Unable to delete medicine.");
            }
        })
        .catch(err => showToast("danger", "Network Error", "Unable to complete delete request."));
};

window.openAddBatchModalForMed = function(medId) {
    document.getElementById("batchForm").reset();
    document.getElementById("batchFormId").value = "";
    document.getElementById("batchModalTitle").innerHTML = '<i class="fa-solid fa-boxes-stacked"></i> Add Medicine Batch';
    populateMedicineSelect("batchFormMedId", medId);
    const todayIso = new Date().toISOString().split("T")[0];
    document.getElementById("batchFormReceived").value = todayIso;
    openModal("batchModal");
};

window.openDispenseForMed = function(medId, specificBatchId = null) {
    document.getElementById("dispenseForm").reset();
    populateMedicineSelect("dispenseMedId", medId);
    const todayIso = new Date().toISOString().split("T")[0];
    document.getElementById("dispenseDate").value = todayIso;
    updateDispenseBatchOptions(medId);
    if (specificBatchId) {
        setTimeout(() => {
            const batchSelect = document.getElementById("dispenseBatchId");
            if (batchSelect) batchSelect.value = specificBatchId;
        }, 200);
    }
    openModal("dispenseModal");
};

// ========================================================
// BATCH ACTIONS
// ========================================================
window.editBatch = function(batchId) {
    const batch = State.batches.find(b => b.id === batchId);
    if (!batch) return;

    document.getElementById("batchFormId").value = batch.id;
    populateMedicineSelect("batchFormMedId", batch.medicine_id);
    document.getElementById("batchFormNumber").value = batch.batch_number;
    document.getElementById("batchFormQuantity").value = batch.quantity;
    document.getElementById("batchFormExpiry").value = batch.expiry_date;
    document.getElementById("batchFormReceived").value = batch.received_date || "";
    document.getElementById("batchFormSupplier").value = batch.supplier || "";
    document.getElementById("batchFormUnitCost").value = batch.unit_cost || "";
    document.getElementById("batchFormNotes").value = batch.notes || "";

    document.getElementById("batchModalTitle").innerHTML = '<i class="fa-solid fa-pen"></i> Edit Batch Details';
    openModal("batchModal");
};

window.deleteBatch = function(batchId, batchNumber) {
    if (!confirm(`Are you sure you want to delete Batch "${batchNumber}"?`)) {
        return;
    }

    fetch(`/api/batches/${batchId}`, { method: "DELETE" })
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                showToast("success", "Batch Removed", res.message);
                loadBatches();
                loadMedicines();
                loadDashboard();
                loadExpiryAlerts();
            } else {
                showToast("danger", "Failed", res.error);
            }
        })
        .catch(err => showToast("danger", "Network Error", "Unable to complete request."));
};

window.quarantineBatch = function(batchId, batchNumber) {
    if (!confirm(`Quarantine & dispose expired Batch "${batchNumber}"? This will set remaining quantity to 0 and record the disposal in storage audit notes.`)) {
        return;
    }

    fetch(`/api/batches/${batchId}/quarantine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Disposed / Quarantined by clinic manager on " + new Date().toISOString().split("T")[0] })
    })
    .then(res => res.json())
    .then(res => {
        if (res.success) {
            showToast("warning", "Quarantined", `Batch ${batchNumber} quarantined & disposed.`);
            closeModal("medDetailsModal");
            loadBatches();
            loadMedicines();
            loadDashboard();
            loadExpiryAlerts();
        } else {
            showToast("danger", "Error", res.error);
        }
    })
    .catch(err => showToast("danger", "Network Error", "Unable to complete request."));
};

function resetSampleData() {
    fetch("/api/reset-data", { method: "POST" })
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                showToast("info", "Sample Data Reset", "Loaded fresh sample clinic medicines, batches and usage records.");
                loadAllData();
                refreshCurrentView(State.currentView);
            }
        })
        .catch(err => showToast("danger", "Network Error", "Failed to reset sample data."));
}

// Utility: HTML Escaping
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
