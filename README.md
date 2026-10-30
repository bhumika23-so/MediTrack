# MediTrack – Smart Medicine Inventory Monitoring System

A complete healthcare inventory and safety monitoring application engineered for small clinics, dispensaries, and healthcare centers to monitor medicine stocks, prevent stockouts, and proactively identify medicines nearing expiry.

---

## 📋 Problem Statement & Purpose

Small clinics frequently face stock monitoring challenges:
- High risks of dispensing expired medicines due to lack of batch-level tracking.
- Critical shortages occurring unexpectedly because average daily consumption rates are not analyzed.
- Financial waste from expired medications expiring unnoticed on back shelves.

**MediTrack solves these problems with:**
1. **Batch-Wise Expiry & Stock Tracking** — Every batch has its own expiry date, quantity, and supplier history.
2. **Clinical Safety Rule** — *Expired batches are NEVER counted as usable stock* and cannot be dispensed.
3. **Automated 30-Day Expiry Alerts** — Color-coded countdown alerts and dedicated quarantine views for expired stock.
4. **Low Stock Warnings** — Real-time alerts when usable inventory dips below minimum safety thresholds.
5. **Consumption-Based Shortage Prediction** — Calculates velocity of consumption over 30 days and forecasts exact days until stock depletion.
6. **FEFO (First-Expiring-First-Out) Dispensing** — Automatically suggests the earliest expiring batches first to reduce medicine waste.

---

## 🛠️ Technology Stack

- **Backend:** Python (Flask web framework, RESTful API architecture)
- **Database:** SQLite3 (Lightweight, zero-setup, reliable relational database with foreign key integrity)
- **Frontend:** HTML5, CSS3, Modern Vanilla JavaScript (Single-Page Dashboard architecture)
- **Visualizations:** Chart.js 4 (Interactive doughnut, grouped bar, and safety ratio charts)
- **Icons & Typography:** Font Awesome 6, Google Fonts Inter

---

## 📁 Project Structure

```
mediTrack/
│
├── app.py                     # Flask application, routing & complete REST API
├── database.py                # SQLite schema setup & realistic sample data seeder
├── run.py                     # Quick startup launcher
├── requirements.txt           # Python dependencies (Flask)
│
├── static/
│   ├── css/
│   │   └── style.css          # Healthcare UI theme (blue, teal, white, light-grey)
│   └── js/
│       ├── app.js             # Frontend controller, API integration, modals, alerts
│       └── charts.js          # Chart.js visualizations & dashboard analytics
│
├── templates/
│   └── index.html             # Main dashboard template with responsive sidebar & modals
│
└── README.md                  # Comprehensive documentation
```

---

## 🚀 Quickstart Guide

### 1. Requirements
Ensure you have **Python 3.8+** installed on your system.

### 2. Install Dependencies
Open your terminal in the `mediTrack` directory and install Flask:

```bash
pip install -r requirements.txt
```

### 3. Start MediTrack
Run the launcher script:

```bash
python run.py
```
*(Or `python app.py`)*

### 4. Access the Application
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

The database (`meditrack.db`) will be automatically initialized and pre-seeded with realistic clinic inventory data on first launch!

---

## 🩺 Core Features & Workflow

### 1. Medicine Management
- Add, edit, delete, and search medicines.
- Track medicine name, category, dispensing unit (tablets, capsules, bottles, inhalers, etc.), and minimum stock safety level.
- Live search by name and filter by category or stock condition.

### 2. Batch & Stock Management
- Support for multiple batches per medicine with distinct batch numbers, quantities, expiry dates, supplier information, and purchase dates.
- Clear distinction between **Usable Stock** and **Physical Stock**.
- **Clinical Safety Rule Strictly Enforced:** Batches whose expiry date has passed are excluded from usable stock.

### 3. Expiry Alerts & Quarantine
- **Expiring Soon (Within 30 Days):** Highlighted with warning indicators, showing exact days remaining until expiration.
- **Expired Medicines:** Displayed in a dedicated separate view with quarantine/disposal actions so clinic managers can audit and safely remove them.

### 4. Low Stock Alerts
- **Completely Out of Stock:** Immediate critical alert when usable stock is 0 units.
- **Below Minimum Threshold:** Warning badge displaying stock capacity percentage and units needed to return to safe levels.

### 5. Inventory Analytics (Chart.js)
- **Usable Stock by Category:** Interactive doughnut chart displaying distribution across Antibiotics, Analgesics, Antidiabetics, Cardiovascular, etc.
- **Stock vs Minimum Level:** Grouped bar chart comparing current usable stock against safety thresholds.
- **Expiry Health Ratio:** Real-time breakdown of Good vs Expiring Soon vs Expired batches.

### 6. Stock Shortage Prediction
- Analyzes recent 30-day clinic consumption logs.
- Calculates **Average Daily Usage** = `Units Consumed / 30 Days`.
- Predicts **Days Until Stockout** = `Usable Stock / Average Daily Usage`.
- Flags urgency levels:
  - 🚨 **Critical Shortage:** &le; 7 days of supply remaining.
  - ⚠️ **Moderate Shortage:** 8 to 15 days of supply remaining.
  - 🟢 **Safe:** > 15 days of supply remaining.
- Generates **Suggested Reorder Quantities** to maintain a 30-day buffer.

### 7. Dispensing & FEFO Allocation
- Record medicine dispensing to outpatient clinics or prescriptions.
- Automatic **First-Expiring-First-Out (FEFO)** selection to prioritize earlier expiring batches.
- Complete audit trail under the "Dispense History" tab.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check and current date |
| `GET` | `/api/medicines` | List all medicines with calculated usable & expired stocks |
| `POST` | `/api/medicines` | Register a new medicine |
| `GET` | `/api/medicines/<id>` | Get single medicine details with all its batches |
| `PUT` | `/api/medicines/<id>` | Update medicine details |
| `DELETE` | `/api/medicines/<id>` | Delete medicine and all its batches |
| `GET` | `/api/batches` | List batches (filterable by `medicine_id` or `status`) |
| `POST` | `/api/batches` | Add new stock batch |
| `PUT` | `/api/batches/<id>` | Update batch details |
| `DELETE` | `/api/batches/<id>` | Delete a batch |
| `POST` | `/api/batches/<id>/quarantine` | Quarantine and dispose an expired batch |
| `GET` | `/api/alerts/expiry` | Expiring soon (&le;30d) and expired medicines |
| `GET` | `/api/alerts/low-stock` | Medicines below minimum threshold or out of stock |
| `GET` | `/api/analytics/predictions`| Daily usage velocity & days until stockout forecast |
| `GET` | `/api/analytics/summary` | High-level KPI metrics & chart datasets |
| `GET` | `/api/consumption` | Recent dispensing logs |
| `POST` | `/api/consumption` | Record medicine dispense (FEFO deduction) |
| `POST` | `/api/reset-data` | Reset sample clinic database |

---

## 🏥 Design Guidelines

- **Healthcare Palette:** Professional Royal Blue (`#2563EB`), Medical Teal (`#0284C7`), Crisp White, and Neutral Slate Slate (`#0F172A`).
- **Responsive Layout:** Sidebar collapsible on mobile screens, adaptive data tables, clean modal dialogs.
- **Accessibility & Safety:** High-contrast badges, clear distinction between active usable stock and expired units.
