"""
MediTrack – Smart Medicine Inventory Monitoring System
Backend Flask Application & REST API
"""

from flask import Flask, render_template, request, jsonify
from datetime import date, datetime, timedelta
import math
import os
import sqlite3

from database import get_db_connection, init_db, seed_sample_data

app = Flask(__name__)
app.config["SECRET_KEY"] = "meditrack-secret-healthcare-key-2024"

# Initialize database and auto-seed if empty
with app.app_context():
    init_db()
    seed_sample_data()


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def get_today():
    """Returns today's date object."""
    return date.today()

def parse_date(date_str):
    """Safely parse YYYY-MM-DD string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def compute_batch_status(expiry_date_str, today=None):
    """
    Computes batch status relative to today:
    - 'EXPIRED': expiry_date < today
    - 'EXPIRING_SOON': today <= expiry_date <= today + 30 days
    - 'GOOD': expiry_date > today + 30 days
    """
    if today is None:
        today = get_today()
    
    exp_date = parse_date(expiry_date_str)
    if not exp_date:
        return {"status": "UNKNOWN", "days_remaining": 0, "badge_class": "badge-gray"}
    
    days_remaining = (exp_date - today).days
    
    if days_remaining < 0:
        return {
            "status": "EXPIRED",
            "days_remaining": days_remaining,
            "abs_days": abs(days_remaining),
            "label": f"Expired {abs(days_remaining)}d ago",
            "badge_class": "badge-danger",
            "is_usable": False
        }
    elif days_remaining <= 30:
        return {
            "status": "EXPIRING_SOON",
            "days_remaining": days_remaining,
            "abs_days": days_remaining,
            "label": f"Expires in {days_remaining}d" if days_remaining > 0 else "Expires today",
            "badge_class": "badge-warning",
            "is_usable": True
        }
    else:
        return {
            "status": "GOOD",
            "days_remaining": days_remaining,
            "abs_days": days_remaining,
            "label": f"{days_remaining}d left",
            "badge_class": "badge-success",
            "is_usable": True
        }


# ---------------------------------------------------------
# Web Routes
# ---------------------------------------------------------

@app.route("/")
def index():
    """Serves the primary Single-Page Dashboard application."""
    return render_template("index.html")

@app.route("/api/health")
def health():
    """System health check endpoint."""
    return jsonify({
        "status": "online",
        "app": "MediTrack",
        "current_date": get_today().isoformat()
    })


# ---------------------------------------------------------
# Medicine Endpoints
# ---------------------------------------------------------

@app.route("/api/medicines", methods=["GET"])
def get_medicines():
    """
    Returns list of all medicines with calculated usable stock,
    expired stock, status, and batch counts.
    Never counts expired batches as usable stock!
    """
    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query all medicines
    cursor.execute("SELECT * FROM medicines ORDER BY name ASC")
    med_rows = cursor.fetchall()

    # Query all batches
    cursor.execute("SELECT * FROM batches ORDER BY expiry_date ASC")
    batch_rows = cursor.fetchall()
    conn.close()

    # Group batches by medicine_id
    batches_by_med = {}
    for b in batch_rows:
        b_dict = dict(b)
        med_id = b_dict["medicine_id"]
        status_info = compute_batch_status(b_dict["expiry_date"], today)
        b_dict.update(status_info)
        
        if med_id not in batches_by_med:
            batches_by_med[med_id] = []
        batches_by_med[med_id].append(b_dict)

    result = []
    for m in med_rows:
        med = dict(m)
        med_id = med["id"]
        med_batches = batches_by_med.get(med_id, [])

        # Usable stock: ONLY non-expired batches with quantity > 0
        usable_stock = 0
        expired_stock = 0
        has_expiring_soon = False
        has_expired = False

        for b in med_batches:
            qty = b["quantity"]
            if b["status"] == "EXPIRED":
                if qty > 0:
                    expired_stock += qty
                has_expired = True
            else:
                usable_stock += qty
                if b["status"] == "EXPIRING_SOON" and qty > 0:
                    has_expiring_soon = True

        # Stock status evaluation based solely on usable stock
        min_stock = med["min_stock"]
        if usable_stock == 0:
            stock_status = "OUT_OF_STOCK"
            stock_badge = "badge-danger"
            stock_label = "Out of Stock"
        elif usable_stock < min_stock:
            stock_status = "LOW_STOCK"
            stock_badge = "badge-warning"
            stock_label = f"Low Stock ({usable_stock}/{min_stock})"
        else:
            stock_status = "IN_STOCK"
            stock_badge = "badge-success"
            stock_label = "In Stock"

        med.update({
            "usable_stock": usable_stock,
            "expired_stock": expired_stock,
            "total_physical_stock": usable_stock + expired_stock,
            "batch_count": len(med_batches),
            "stock_status": stock_status,
            "stock_badge": stock_badge,
            "stock_label": stock_label,
            "has_expiring_soon": has_expiring_soon,
            "has_expired": has_expired,
            "batches": med_batches
        })
        result.append(med)

    return jsonify({"success": True, "medicines": result})


@app.route("/api/medicines", methods=["POST"])
def add_medicine():
    """Creates a new medicine record."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    unit = data.get("unit", "Tablets").strip()
    min_stock = data.get("min_stock", 20)
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"success": False, "error": "Medicine name is required."}), 400
    if not category:
        return jsonify({"success": False, "error": "Category is required."}), 400

    try:
        min_stock = int(min_stock)
        if min_stock < 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Minimum stock level must be a non-negative integer."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO medicines (name, category, unit, min_stock, description) VALUES (?, ?, ?, ?, ?)",
            (name, category, unit, min_stock, description)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({"success": True, "message": "Medicine added successfully.", "id": new_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": f"Medicine with name '{name}' already exists."}), 409
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines/<int:med_id>", methods=["GET"])
def get_medicine_detail(med_id):
    """Retrieves single medicine detail along with its batches and consumption."""
    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
    med_row = cursor.fetchone()
    if not med_row:
        conn.close()
        return jsonify({"success": False, "error": "Medicine not found."}), 404

    med = dict(med_row)

    # Batches
    cursor.execute("SELECT * FROM batches WHERE medicine_id = ? ORDER BY expiry_date ASC", (med_id,))
    batch_rows = cursor.fetchall()
    
    batches = []
    usable_stock = 0
    expired_stock = 0
    for b in batch_rows:
        b_dict = dict(b)
        status_info = compute_batch_status(b_dict["expiry_date"], today)
        b_dict.update(status_info)
        if b_dict["status"] == "EXPIRED":
            if b_dict["quantity"] > 0:
                expired_stock += b_dict["quantity"]
        else:
            usable_stock += b_dict["quantity"]
        batches.append(b_dict)

    # Recent consumption logs
    cursor.execute(
        "SELECT * FROM consumption_logs WHERE medicine_id = ? ORDER BY dispensed_date DESC LIMIT 10",
        (med_id,)
    )
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    med.update({
        "usable_stock": usable_stock,
        "expired_stock": expired_stock,
        "batches": batches,
        "recent_consumption": logs
    })
    return jsonify({"success": True, "medicine": med})


@app.route("/api/medicines/<int:med_id>", methods=["PUT"])
def update_medicine(med_id):
    """Updates medicine metadata."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    unit = data.get("unit", "Tablets").strip()
    min_stock = data.get("min_stock", 20)
    description = data.get("description", "").strip()

    if not name or not category:
        return jsonify({"success": False, "error": "Medicine name and category are required."}), 400

    try:
        min_stock = int(min_stock)
        if min_stock < 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Minimum stock level must be a non-negative integer."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE medicines 
            SET name = ?, category = ?, unit = ?, min_stock = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, category, unit, min_stock, description, med_id))
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "error": "Medicine not found."}), 404
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Medicine updated successfully."})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": f"Another medicine with name '{name}' already exists."}), 409
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/medicines/<int:med_id>", methods=["DELETE"])
def delete_medicine(med_id):
    """Deletes medicine and cascades to its batches and consumption logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "error": "Medicine not found."}), 404
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Medicine and all associated batches deleted successfully."})


# ---------------------------------------------------------
# Batches & Stock Management Endpoints
# ---------------------------------------------------------

@app.route("/api/batches", methods=["GET"])
def get_batches():
    """Returns all batches with medicine information and expiry status."""
    today = get_today()
    med_id = request.args.get("medicine_id")
    status_filter = request.args.get("status")  # 'expired', 'expiring_soon', 'good'

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT b.*, m.name AS medicine_name, m.category, m.unit, m.min_stock
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.id
    """
    params = []
    if med_id:
        sql += " WHERE b.medicine_id = ?"
        params.append(med_id)
    sql += " ORDER BY b.expiry_date ASC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    batches = []
    for r in rows:
        b = dict(r)
        status_info = compute_batch_status(b["expiry_date"], today)
        b.update(status_info)

        # Optional status filtering
        if status_filter:
            if status_filter.upper() != b["status"]:
                continue

        batches.append(b)

    return jsonify({"success": True, "batches": batches})


@app.route("/api/batches", methods=["POST"])
def add_batch():
    """Adds a new stock batch for a medicine."""
    data = request.get_json() or {}
    medicine_id = data.get("medicine_id")
    batch_number = data.get("batch_number", "").strip().upper()
    quantity = data.get("quantity")
    expiry_date = data.get("expiry_date", "").strip()
    received_date = data.get("received_date", "").strip() or get_today().isoformat()
    supplier = data.get("supplier", "").strip()
    unit_cost = data.get("unit_cost", 0.0)
    notes = data.get("notes", "").strip()

    if not medicine_id:
        return jsonify({"success": False, "error": "Medicine selection is required."}), 400
    if not batch_number:
        return jsonify({"success": False, "error": "Batch number is required."}), 400
    if not expiry_date:
        return jsonify({"success": False, "error": "Expiry date is required."}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({"success": False, "error": "Quantity must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid quantity."}), 400

    try:
        unit_cost = float(unit_cost) if unit_cost else 0.0
    except (ValueError, TypeError):
        unit_cost = 0.0

    if not parse_date(expiry_date):
        return jsonify({"success": False, "error": "Expiry date must be in YYYY-MM-DD format."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check medicine exists
    cursor.execute("SELECT id FROM medicines WHERE id = ?", (medicine_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Selected medicine does not exist."}), 404

    try:
        cursor.execute("""
            INSERT INTO batches (
                medicine_id, batch_number, quantity, initial_quantity,
                expiry_date, received_date, supplier, unit_cost, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            medicine_id, batch_number, quantity, quantity,
            expiry_date, received_date, supplier, unit_cost, notes
        ))
        conn.commit()
        batch_id = cursor.lastrowid
        conn.close()
        return jsonify({"success": True, "message": "Batch added successfully.", "id": batch_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": f"Batch number '{batch_number}' already exists."}), 409
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/batches/<int:batch_id>", methods=["PUT"])
def update_batch(batch_id):
    """Updates batch details."""
    data = request.get_json() or {}
    batch_number = data.get("batch_number", "").strip().upper()
    quantity = data.get("quantity")
    expiry_date = data.get("expiry_date", "").strip()
    received_date = data.get("received_date", "").strip()
    supplier = data.get("supplier", "").strip()
    unit_cost = data.get("unit_cost")
    notes = data.get("notes", "").strip()

    if not batch_number or not expiry_date:
        return jsonify({"success": False, "error": "Batch number and expiry date are required."}), 400

    try:
        quantity = int(quantity)
        if quantity < 0:
            return jsonify({"success": False, "error": "Quantity cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid quantity value."}), 400

    try:
        unit_cost = float(unit_cost) if unit_cost is not None else 0.0
    except (ValueError, TypeError):
        unit_cost = 0.0

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE batches
            SET batch_number = ?, quantity = ?, expiry_date = ?, received_date = ?,
                supplier = ?, unit_cost = ?, notes = ?
            WHERE id = ?
        """, (batch_number, quantity, expiry_date, received_date, supplier, unit_cost, notes, batch_id))
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "error": "Batch not found."}), 404
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Batch updated successfully."})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": f"Batch number '{batch_number}' already in use."}), 409
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/batches/<int:batch_id>", methods=["DELETE"])
def delete_batch(batch_id):
    """Deletes a batch."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "error": "Batch not found."}), 404
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Batch removed successfully."})


@app.route("/api/batches/<int:batch_id>/quarantine", methods=["POST"])
def quarantine_batch(batch_id):
    """
    Quarantines an expired batch by zeroing its quantity and recording disposal notes.
    Prevents expired batch from cluttering inventory while keeping history.
    """
    data = request.get_json() or {}
    disposal_notes = data.get("notes", "Quarantined / Disposed due to expiration.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()
    if not batch:
        conn.close()
        return jsonify({"success": False, "error": "Batch not found."}), 404

    cursor.execute("""
        UPDATE batches 
        SET quantity = 0, notes = notes || ' | ' || ?
        WHERE id = ?
    """, (disposal_notes, batch_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Batch quarantined & removed from physical stock."})


# ---------------------------------------------------------
# Expiry Alerts Endpoints
# ---------------------------------------------------------

@app.route("/api/alerts/expiry", methods=["GET"])
def get_expiry_alerts():
    """
    Returns separate lists for:
    1. Expiring soon medicines/batches (0 <= days_to_expiry <= 30)
    2. Expired medicines/batches (days_to_expiry < 0)
    Shows batch-wise expiry dates clearly.
    """
    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.*, m.name AS medicine_name, m.category, m.unit, m.min_stock
        FROM batches b
        JOIN medicines m ON b.medicine_id = m.id
        WHERE b.quantity > 0
        ORDER BY b.expiry_date ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    expiring_soon = []
    expired = []
    wasted_cost = 0.0
    wasted_units = 0

    for r in rows:
        b = dict(r)
        status_info = compute_batch_status(b["expiry_date"], today)
        b.update(status_info)

        if b["status"] == "EXPIRED":
            expired.append(b)
            wasted_units += b["quantity"]
            wasted_cost += b["quantity"] * (b["unit_cost"] or 0.0)
        elif b["status"] == "EXPIRING_SOON":
            expiring_soon.append(b)

    return jsonify({
        "success": True,
        "expiring_soon": expiring_soon,
        "expired": expired,
        "summary": {
            "expiring_soon_count": len(expiring_soon),
            "expired_count": len(expired),
            "wasted_units": wasted_units,
            "wasted_cost": round(wasted_cost, 2),
            "check_date": today.isoformat()
        }
    })


# ---------------------------------------------------------
# Low Stock Alerts Endpoints
# ---------------------------------------------------------

@app.route("/api/alerts/low-stock", methods=["GET"])
def get_low_stock_alerts():
    """
    Identifies medicines whose usable stock is below their minimum stock level.
    Never counts expired batches as usable stock!
    """
    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM medicines ORDER BY name ASC")
    meds = cursor.fetchall()

    cursor.execute("SELECT * FROM batches ORDER BY expiry_date ASC")
    batches = cursor.fetchall()
    conn.close()

    # Calculate usable stock per medicine
    usable_stock_map = {}
    for b in batches:
        b_dict = dict(b)
        status = compute_batch_status(b_dict["expiry_date"], today)
        if status["is_usable"]:
            usable_stock_map[b_dict["medicine_id"]] = (
                usable_stock_map.get(b_dict["medicine_id"], 0) + b_dict["quantity"]
            )

    low_stock_items = []
    out_of_stock_items = []

    for m in meds:
        m_dict = dict(m)
        med_id = m_dict["id"]
        usable = usable_stock_map.get(med_id, 0)
        min_lvl = m_dict["min_stock"]

        m_dict["usable_stock"] = usable
        m_dict["deficit"] = max(0, min_lvl - usable)

        if usable == 0:
            m_dict["urgency"] = "CRITICAL"
            m_dict["urgency_label"] = "Completely Out of Stock"
            out_of_stock_items.append(m_dict)
        elif usable < min_lvl:
            pct = round((usable / min_lvl) * 100, 1)
            m_dict["stock_percentage"] = pct
            m_dict["urgency"] = "WARNING"
            m_dict["urgency_label"] = f"{pct}% of Minimum Level"
            low_stock_items.append(m_dict)

    return jsonify({
        "success": True,
        "out_of_stock": out_of_stock_items,
        "low_stock": low_stock_items,
        "summary": {
            "out_of_stock_count": len(out_of_stock_items),
            "low_stock_count": len(low_stock_items),
            "total_alerts": len(out_of_stock_items) + len(low_stock_items)
        }
    })


# ---------------------------------------------------------
# Stock Shortage Prediction Endpoints
# ---------------------------------------------------------

@app.route("/api/analytics/predictions", methods=["GET"])
def get_shortage_predictions():
    """
    Calculates average daily usage from consumption data and predicts
    how many days available usable stock will last.
    Flags potential shortages.
    """
    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM medicines ORDER BY name ASC")
    meds = [dict(m) for m in cursor.fetchall()]

    cursor.execute("SELECT * FROM batches ORDER BY expiry_date ASC")
    batches = [dict(b) for b in cursor.fetchall()]

    # Consumption in past 30 days
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    cursor.execute("""
        SELECT medicine_id, SUM(quantity) AS total_consumed, COUNT(*) AS log_count
        FROM consumption_logs
        WHERE dispensed_date >= ?
        GROUP BY medicine_id
    """, (thirty_days_ago,))
    consumption_map = {row["medicine_id"]: dict(row) for row in cursor.fetchall()}
    conn.close()

    # Calculate usable stock
    usable_map = {}
    for b in batches:
        st = compute_batch_status(b["expiry_date"], today)
        if st["is_usable"]:
            usable_map[b["medicine_id"]] = usable_map.get(b["medicine_id"], 0) + b["quantity"]

    predictions = []
    critical_shortages = 0
    moderate_shortages = 0

    for m in meds:
        med_id = m["id"]
        usable = usable_map.get(med_id, 0)
        c_info = consumption_map.get(med_id, {"total_consumed": 0, "log_count": 0})
        total_30d = c_info["total_consumed"] or 0
        avg_daily = round(total_30d / 30.0, 2)

        if usable == 0:
            days_remaining = 0
            risk = "OUT_OF_STOCK"
            risk_badge = "badge-danger"
            risk_label = "0 Days (Stockout)"
            reorder_qty = math.ceil(max(avg_daily * 30, m["min_stock"]))
            critical_shortages += 1
        elif avg_daily > 0:
            days_remaining = round(usable / avg_daily, 1)
            # Reorder quantity to maintain 30-day target buffer
            target_buffer = max(avg_daily * 30, m["min_stock"])
            reorder_qty = math.ceil(max(0, target_buffer - usable))

            if days_remaining <= 7:
                risk = "CRITICAL_SHORTAGE"
                risk_badge = "badge-danger"
                risk_label = f"Shortage in {days_remaining}d"
                critical_shortages += 1
            elif days_remaining <= 15:
                risk = "MODERATE_SHORTAGE"
                risk_badge = "badge-warning"
                risk_label = f"Shortage in {days_remaining}d"
                moderate_shortages += 1
            elif days_remaining <= 30:
                risk = "MODERATE_STOCK"
                risk_badge = "badge-info"
                risk_label = f"Lasts {days_remaining}d"
            else:
                risk = "SAFE_STOCK"
                risk_badge = "badge-success"
                risk_label = f"Safe ({days_remaining}d)"
        else:
            days_remaining = None
            risk = "NO_USAGE_DATA"
            risk_badge = "badge-gray"
            risk_label = "No Recent Usage"
            reorder_qty = max(0, m["min_stock"] - usable)

        predictions.append({
            "medicine_id": med_id,
            "name": m["name"],
            "category": m["category"],
            "unit": m["unit"],
            "min_stock": m["min_stock"],
            "usable_stock": usable,
            "consumption_30d": total_30d,
            "avg_daily_usage": avg_daily,
            "days_remaining": days_remaining,
            "risk": risk,
            "risk_badge": risk_badge,
            "risk_label": risk_label,
            "reorder_qty": reorder_qty
        })

    # Sort predictions by urgency (lowest days_remaining first, None at the end)
    def sort_key(item):
        if item["days_remaining"] is None:
            return 9999
        return item["days_remaining"]

    predictions.sort(key=sort_key)

    return jsonify({
        "success": True,
        "predictions": predictions,
        "summary": {
            "critical_shortages": critical_shortages,
            "moderate_shortages": moderate_shortages,
            "total_medicines_analyzed": len(predictions)
        }
    })


# ---------------------------------------------------------
# Usage Consumption / Dispensing Endpoints
# ---------------------------------------------------------

@app.route("/api/consumption", methods=["GET"])
def get_consumption_logs():
    """Returns recent medicine consumption history."""
    limit = request.args.get("limit", 20, type=int)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.*, m.name AS medicine_name, m.unit, b.batch_number
        FROM consumption_logs c
        JOIN medicines m ON c.medicine_id = m.id
        LEFT JOIN batches b ON c.batch_id = b.id
        ORDER BY c.dispensed_date DESC, c.id DESC
        LIMIT ?
    """, (limit,))
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"success": True, "logs": logs})


@app.route("/api/consumption", methods=["POST"])
def record_consumption():
    """
    Records medicine usage/dispense.
    Deducts stock using FEFO (First-Expiring-First-Out) from usable non-expired batches!
    Never dispenses expired batches.
    """
    data = request.get_json() or {}
    medicine_id = data.get("medicine_id")
    quantity_to_dispense = data.get("quantity")
    batch_id = data.get("batch_id")  # Optional specific batch
    dispensed_to = data.get("dispensed_to", "General Outpatient Dispense").strip()
    dispensed_date = data.get("dispensed_date", "").strip() or get_today().isoformat()

    if not medicine_id:
        return jsonify({"success": False, "error": "Medicine ID is required."}), 400

    try:
        quantity_to_dispense = int(quantity_to_dispense)
        if quantity_to_dispense <= 0:
            return jsonify({"success": False, "error": "Quantity must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid quantity."}), 400

    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get non-expired batches with positive quantity
    # FEFO: Order by expiry_date ASC
    cursor.execute("""
        SELECT * FROM batches 
        WHERE medicine_id = ? AND quantity > 0 AND expiry_date >= ?
        ORDER BY expiry_date ASC
    """, (medicine_id, today.isoformat()))
    usable_batches = [dict(b) for b in cursor.fetchall()]

    if not usable_batches:
        conn.close()
        return jsonify({
            "success": False, 
            "error": "No non-expired usable batches available for this medicine!"
        }), 400

    total_available = sum(b["quantity"] for b in usable_batches)
    if total_available < quantity_to_dispense:
        conn.close()
        return jsonify({
            "success": False, 
            "error": f"Insufficient usable stock. Only {total_available} units available."
        }), 400

    remaining_to_deduct = quantity_to_dispense

    # If specific batch requested
    if batch_id:
        cursor.execute("""
            SELECT * FROM batches 
            WHERE id = ? AND medicine_id = ? AND expiry_date >= ?
        """, (batch_id, medicine_id, today.isoformat()))
        specific_batch = cursor.fetchone()
        if not specific_batch:
            conn.close()
            return jsonify({"success": False, "error": "Specified batch is either expired, invalid or has no stock."}), 400
        
        if specific_batch["quantity"] < quantity_to_dispense:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Specified batch only has {specific_batch['quantity']} units available."
            }), 400

        cursor.execute(
            "UPDATE batches SET quantity = quantity - ? WHERE id = ?",
            (quantity_to_dispense, batch_id)
        )
        cursor.execute("""
            INSERT INTO consumption_logs (medicine_id, batch_id, quantity, dispensed_to, dispensed_date)
            VALUES (?, ?, ?, ?, ?)
        """, (medicine_id, batch_id, quantity_to_dispense, dispensed_to, dispensed_date))
    else:
        # Automatic FEFO allocation across earliest expiring batches
        for b in usable_batches:
            if remaining_to_deduct <= 0:
                break
            deduct_now = min(b["quantity"], remaining_to_deduct)
            cursor.execute(
                "UPDATE batches SET quantity = quantity - ? WHERE id = ?",
                (deduct_now, b["id"])
            )
            cursor.execute("""
                INSERT INTO consumption_logs (medicine_id, batch_id, quantity, dispensed_to, dispensed_date)
                VALUES (?, ?, ?, ?, ?)
            """, (medicine_id, b["id"], deduct_now, dispensed_to, dispensed_date))
            remaining_to_deduct -= deduct_now

    conn.commit()
    conn.close()

    return jsonify({
        "success": True, 
        "message": f"Successfully dispensed {quantity_to_dispense} units."
    })


# ---------------------------------------------------------
# Inventory Analytics & Dashboard Summary Endpoints
# ---------------------------------------------------------

@app.route("/api/analytics/summary", methods=["GET"])
def get_dashboard_summary():
    """
    Returns high-level KPI cards and chart data for the dashboard:
    - Total medicines
    - Total usable stock (strictly non-expired)
    - Expiring soon batches count
    - Expired batches count & units
    - Low stock medicine count
    - Critical shortage risk count
    - Category distribution
    - Expiry status breakdown
    """
    today = get_today()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM medicines")
    meds = [dict(m) for m in cursor.fetchall()]

    cursor.execute("SELECT * FROM batches")
    batches = [dict(b) for b in cursor.fetchall()]

    # 30-day consumption
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    cursor.execute("""
        SELECT medicine_id, SUM(quantity) AS total_consumed
        FROM consumption_logs
        WHERE dispensed_date >= ?
        GROUP BY medicine_id
    """, (thirty_days_ago,))
    consumption_map = {row["medicine_id"]: row["total_consumed"] for row in cursor.fetchall()}
    conn.close()

    total_medicines = len(meds)
    total_usable_stock = 0
    total_expired_stock = 0
    expiring_soon_count = 0
    expired_batch_count = 0
    good_batch_count = 0

    usable_per_med = {}
    category_stock = {}

    for b in batches:
        st = compute_batch_status(b["expiry_date"], today)
        qty = b["quantity"]

        if st["status"] == "EXPIRED":
            if qty > 0:
                expired_batch_count += 1
                total_expired_stock += qty
        elif st["status"] == "EXPIRING_SOON":
            if qty > 0:
                expiring_soon_count += 1
                total_usable_stock += qty
                usable_per_med[b["medicine_id"]] = usable_per_med.get(b["medicine_id"], 0) + qty
        else: # GOOD
            if qty > 0:
                good_batch_count += 1
                total_usable_stock += qty
                usable_per_med[b["medicine_id"]] = usable_per_med.get(b["medicine_id"], 0) + qty

    low_stock_count = 0
    out_of_stock_count = 0
    critical_shortage_count = 0

    # Stock by medicine & Category aggregation
    med_stock_comparison = []
    for m in meds:
        med_id = m["id"]
        cat = m["category"]
        usable = usable_per_med.get(med_id, 0)
        category_stock[cat] = category_stock.get(cat, 0) + usable

        min_lvl = m["min_stock"]
        if usable == 0:
            out_of_stock_count += 1
            low_stock_count += 1
            critical_shortage_count += 1
        elif usable < min_lvl:
            low_stock_count += 1

        # Calculate shortage prediction
        c_30d = consumption_map.get(med_id, 0)
        if c_30d > 0 and usable > 0:
            avg_d = c_30d / 30.0
            if (usable / avg_d) <= 7:
                critical_shortage_count += 1

        med_stock_comparison.append({
            "name": m["name"],
            "usable_stock": usable,
            "min_stock": min_lvl
        })

    # Sort med comparison by usable stock ascending to highlight those closest to zero
    med_stock_comparison.sort(key=lambda x: x["usable_stock"])

    return jsonify({
        "success": True,
        "kpis": {
            "total_medicines": total_medicines,
            "total_usable_stock": total_usable_stock,
            "total_expired_stock": total_expired_stock,
            "expiring_soon_count": expiring_soon_count,
            "expired_batch_count": expired_batch_count,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "critical_shortage_count": critical_shortage_count,
            "today_date": today.isoformat()
        },
        "charts": {
            "categories": {
                "labels": list(category_stock.keys()),
                "data": list(category_stock.values())
            },
            "expiry_breakdown": {
                "labels": ["Good / Safe (>30d)", "Expiring Soon (<=30d)", "Expired"],
                "data": [good_batch_count, expiring_soon_count, expired_batch_count]
            },
            "stock_comparison": {
                "labels": [m["name"] for m in med_stock_comparison[:8]],
                "usable": [m["usable_stock"] for m in med_stock_comparison[:8]],
                "minimum": [m["min_stock"] for m in med_stock_comparison[:8]]
            }
        }
    })


@app.route("/api/reset-data", methods=["POST"])
def reset_database():
    """Resets database with fresh realistic sample data."""
    seed_sample_data(force=True)
    return jsonify({"success": True, "message": "Database successfully reset to initial sample clinic data."})


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
