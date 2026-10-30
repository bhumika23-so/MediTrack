"""
database.py - SQLite Database Configuration & Sample Data Seeder for MediTrack
"""

import sqlite3
import os
from datetime import date, timedelta
import random

DB_NAME = "meditrack.db"

def get_db_path():
    """Returns the absolute path to the SQLite database file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)

def get_db_connection():
    """Establishes and returns a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Medicines Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        unit TEXT NOT NULL DEFAULT 'Tablets',
        min_stock INTEGER NOT NULL DEFAULT 20,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Batches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER NOT NULL,
        batch_number TEXT NOT NULL UNIQUE,
        quantity INTEGER NOT NULL DEFAULT 0,
        initial_quantity INTEGER NOT NULL DEFAULT 0,
        expiry_date TEXT NOT NULL,
        received_date TEXT NOT NULL,
        supplier TEXT,
        unit_cost REAL DEFAULT 0.0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
    );
    """)

    # 3. Consumption Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consumption_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER NOT NULL,
        batch_id INTEGER,
        quantity INTEGER NOT NULL,
        dispensed_to TEXT,
        dispensed_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
        FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()

def seed_sample_data(force=False):
    """
    Populates the database with realistic sample clinic inventory data.
    Uses relative dates based on current date so test conditions (expired, expiring soon, safe)
    are always accurate whenever run.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) AS cnt FROM medicines")
    count = cursor.fetchone()["cnt"]
    if count > 0 and not force:
        conn.close()
        return False  # Already seeded

    # Clear existing data if force
    if force:
        cursor.execute("DELETE FROM consumption_logs")
        cursor.execute("DELETE FROM batches")
        cursor.execute("DELETE FROM medicines")

    today = date.today()

    # Sample Medicines
    medicines = [
        {"name": "Paracetamol 500mg", "category": "Analgesic & Antipyretic", "unit": "Tablets", "min_stock": 50, "description": "Pain relief and fever reduction"},
        {"name": "Amoxicillin 500mg", "category": "Antibiotic", "unit": "Capsules", "min_stock": 40, "description": "Broad-spectrum penicillin antibiotic"},
        {"name": "Metformin 500mg", "category": "Antidiabetic", "unit": "Tablets", "min_stock": 60, "description": "Type 2 diabetes blood glucose regulation"},
        {"name": "Amlodipine 5mg", "category": "Cardiovascular", "unit": "Tablets", "min_stock": 35, "description": "Hypertension and angina management"},
        {"name": "Omeprazole 20mg", "category": "Gastrointestinal", "unit": "Capsules", "min_stock": 30, "description": "Proton pump inhibitor for acid reflux"},
        {"name": "Cetirizine 10mg", "category": "Antihistamine", "unit": "Tablets", "min_stock": 25, "description": "Allergy and rhinitis relief"},
        {"name": "Azithromycin 250mg", "category": "Antibiotic", "unit": "Tablets", "min_stock": 30, "description": "Macrolide antibiotic for respiratory tract infections"},
        {"name": "Ibuprofen 400mg", "category": "NSAID", "unit": "Tablets", "min_stock": 45, "description": "Anti-inflammatory and moderate pain relief"},
        {"name": "Salbutamol 100mcg", "category": "Respiratory", "unit": "Inhalers", "min_stock": 15, "description": "Bronchodilator for asthma and COPD"},
        {"name": "Atorvastatin 20mg", "category": "Cardiovascular", "unit": "Tablets", "min_stock": 40, "description": "Cholesterol and cardiovascular risk reduction"},
        {"name": "Ciprofloxacin 500mg", "category": "Antibiotic", "unit": "Tablets", "min_stock": 20, "description": "Fluoroquinolone antibiotic for bacterial infections"},
        {"name": "ORS Powder Packets", "category": "Electrolyte", "unit": "Sachets", "min_stock": 25, "description": "Oral rehydration salts for dehydration"}
    ]

    med_id_map = {}
    for med in medicines:
        cursor.execute(
            "INSERT INTO medicines (name, category, unit, min_stock, description) VALUES (?, ?, ?, ?, ?)",
            (med["name"], med["category"], med["unit"], med["min_stock"], med["description"])
        )
        med_id_map[med["name"]] = cursor.lastrowid

    # Sample Batches with calculated dates:
    # - Expired batches: today - 45 days, today - 10 days
    # - Expiring soon: today + 6 days, today + 14 days, today + 25 days
    # - Safe batches: today + 180 days, today + 365 days, today + 500 days
    batches = [
        # Paracetamol (Good stock, multiple batches, one expiring soon)
        {
            "med": "Paracetamol 500mg",
            "batch_no": "PARA-2401",
            "qty": 35,
            "init_qty": 100,
            "expiry": today + timedelta(days=12),   # Expiring soon! (12 days)
            "received": today - timedelta(days=200),
            "supplier": "Apex Pharma Ltd",
            "cost": 0.15,
            "notes": "First shelf batch"
        },
        {
            "med": "Paracetamol 500mg",
            "batch_no": "PARA-2402",
            "qty": 80,
            "init_qty": 100,
            "expiry": today + timedelta(days=240),  # Safe
            "received": today - timedelta(days=30),
            "supplier": "Apex Pharma Ltd",
            "cost": 0.15,
            "notes": "Main storage"
        },
        # Amoxicillin (One expired batch, one active batch with low stock)
        {
            "med": "Amoxicillin 500mg",
            "batch_no": "AMOX-2309",
            "qty": 18,
            "init_qty": 50,
            "expiry": today - timedelta(days=14),   # EXPIRED 14 days ago!
            "received": today - timedelta(days=300),
            "supplier": "MedLife Global",
            "cost": 0.45,
            "notes": "Quarantined in storage room B"
        },
        {
            "med": "Amoxicillin 500mg",
            "batch_no": "AMOX-2403",
            "qty": 15,                              # Low stock! Min stock is 40
            "init_qty": 60,
            "expiry": today + timedelta(days=150),
            "received": today - timedelta(days=45),
            "supplier": "MedLife Global",
            "cost": 0.45,
            "notes": "Dispensing rack"
        },
        # Metformin (Healthy stock)
        {
            "med": "Metformin 500mg",
            "batch_no": "MET-2401",
            "qty": 50,
            "init_qty": 80,
            "expiry": today + timedelta(days=18),   # Expiring soon! (18 days)
            "received": today - timedelta(days=160),
            "supplier": "Sunlight Healthcare",
            "cost": 0.20,
            "notes": "Fast moving"
        },
        {
            "med": "Metformin 500mg",
            "batch_no": "MET-2404",
            "qty": 120,
            "init_qty": 150,
            "expiry": today + timedelta(days=380),  # Safe
            "received": today - timedelta(days=15),
            "supplier": "Sunlight Healthcare",
            "cost": 0.20,
            "notes": "Bulk box"
        },
        # Amlodipine (Low stock alert)
        {
            "med": "Amlodipine 5mg",
            "batch_no": "AML-2402",
            "qty": 10,                              # Low stock! Min stock is 35
            "init_qty": 50,
            "expiry": today + timedelta(days=190),
            "received": today - timedelta(days=90),
            "supplier": "CardioCare Bio",
            "cost": 0.30,
            "notes": "Urgent reorder recommended"
        },
        # Omeprazole (Expired batch + safe batch)
        {
            "med": "Omeprazole 20mg",
            "batch_no": "OMEP-2311",
            "qty": 22,
            "init_qty": 60,
            "expiry": today - timedelta(days=28),   # EXPIRED!
            "received": today - timedelta(days=320),
            "supplier": "Zenith Remedies",
            "cost": 0.50,
            "notes": "Awaiting disposal protocol"
        },
        {
            "med": "Omeprazole 20mg",
            "batch_no": "OMEP-2401",
            "qty": 45,
            "init_qty": 60,
            "expiry": today + timedelta(days=210),  # Safe
            "received": today - timedelta(days=40),
            "supplier": "Zenith Remedies",
            "cost": 0.50,
            "notes": "Active dispenser"
        },
        # Cetirizine (Expiring very soon: 7 days)
        {
            "med": "Cetirizine 10mg",
            "batch_no": "CET-2401",
            "qty": 20,
            "init_qty": 40,
            "expiry": today + timedelta(days=7),    # Expiring in 7 days!
            "received": today - timedelta(days=180),
            "supplier": "AllerGuard Labs",
            "cost": 0.25,
            "notes": "Near front desk"
        },
        {
            "med": "Cetirizine 10mg",
            "batch_no": "CET-2405",
            "qty": 50,
            "init_qty": 50,
            "expiry": today + timedelta(days=300),
            "received": today - timedelta(days=10),
            "supplier": "AllerGuard Labs",
            "cost": 0.25,
            "notes": "New arrival"
        },
        # Azithromycin (Critical Shortage: usable stock = 4, min stock = 30)
        {
            "med": "Azithromycin 250mg",
            "batch_no": "AZI-2401",
            "qty": 4,                               # Critical Shortage!
            "init_qty": 30,
            "expiry": today + timedelta(days=95),
            "received": today - timedelta(days=60),
            "supplier": "MedLife Global",
            "cost": 1.10,
            "notes": "Only 4 tablets left"
        },
        # Ibuprofen (Safe stock)
        {
            "med": "Ibuprofen 400mg",
            "batch_no": "IBU-2402",
            "qty": 75,
            "init_qty": 100,
            "expiry": today + timedelta(days=280),
            "received": today - timedelta(days=50),
            "supplier": "Apex Pharma Ltd",
            "cost": 0.18,
            "notes": "Adequate"
        },
        # Salbutamol (Expiring in 26 days)
        {
            "med": "Salbutamol 100mcg",
            "batch_no": "SALB-2401",
            "qty": 8,                               # Low stock (min 15) and Expiring soon (26 days)!
            "init_qty": 20,
            "expiry": today + timedelta(days=26),
            "received": today - timedelta(days=150),
            "supplier": "RespiCare Instruments",
            "cost": 4.50,
            "notes": "Emergency trolley"
        },
        # Atorvastatin (Healthy)
        {
            "med": "Atorvastatin 20mg",
            "batch_no": "ATOR-2401",
            "qty": 90,
            "init_qty": 100,
            "expiry": today + timedelta(days=400),
            "received": today - timedelta(days=20),
            "supplier": "CardioCare Bio",
            "cost": 0.55,
            "notes": "Stable inventory"
        },
        # Ciprofloxacin (Completely Out of usable Stock / Expired only)
        {
            "med": "Ciprofloxacin 500mg",
            "batch_no": "CIPRO-2308",
            "qty": 12,                              # Expired! So usable stock = 0!
            "init_qty": 40,
            "expiry": today - timedelta(days=40),
            "received": today - timedelta(days=360),
            "supplier": "MedLife Global",
            "cost": 0.80,
            "notes": "Expired - needs immediate restocking"
        },
        # ORS Powder (Safe stock)
        {
            "med": "ORS Powder Packets",
            "batch_no": "ORS-2401",
            "qty": 45,
            "init_qty": 60,
            "expiry": today + timedelta(days=320),
            "received": today - timedelta(days=30),
            "supplier": "Zenith Remedies",
            "cost": 0.35,
            "notes": "Pediatric shelf"
        }
    ]

    batch_id_map = {}
    for b in batches:
        med_id = med_id_map[b["med"]]
        cursor.execute("""
            INSERT INTO batches (
                medicine_id, batch_number, quantity, initial_quantity,
                expiry_date, received_date, supplier, unit_cost, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            med_id, b["batch_no"], b["qty"], b["init_qty"],
            b["expiry"].isoformat(), b["received"].isoformat(),
            b["supplier"], b["cost"], b["notes"]
        ))
        batch_id_map[b["batch_no"]] = cursor.lastrowid

    # Sample Consumption Logs over the last 30 days
    # This enables instant, realistic daily usage calculation and stock shortage predictions
    consumption_records = [
        # Paracetamol: high regular usage (avg ~4-5/day)
        ("Paracetamol 500mg", "PARA-2401", 12, 28, "Outpatient general clinic"),
        ("Paracetamol 500mg", "PARA-2401", 15, 22, "Fever & flu surge"),
        ("Paracetamol 500mg", "PARA-2401", 10, 15, "Post-op analgesia"),
        ("Paracetamol 500mg", "PARA-2401", 18, 9, "Adult OPD walk-in"),
        ("Paracetamol 500mg", "PARA-2401", 10, 3, "Prescriptions refill"),
        # Amoxicillin: moderate usage (~2.5/day)
        ("Amoxicillin 500mg", "AMOX-2403", 10, 25, "Bacterial ENT clinic"),
        ("Amoxicillin 500mg", "AMOX-2403", 12, 17, "Dental infections"),
        ("Amoxicillin 500mg", "AMOX-2403", 15, 8, "Respiratory infections"),
        ("Amoxicillin 500mg", "AMOX-2403", 8, 2, "General prescriptions"),
        # Metformin: steady chronic usage (~3/day)
        ("Metformin 500mg", "MET-2401", 15, 29, "Diabetic clinic monthly refill"),
        ("Metformin 500mg", "MET-2401", 15, 20, "Diabetic clinic monthly refill"),
        ("Metformin 500mg", "MET-2401", 15, 10, "Diabetic clinic monthly refill"),
        ("Metformin 500mg", "MET-2401", 15, 2, "Diabetic clinic monthly refill"),
        # Amlodipine: high steady chronic usage (~2/day)
        ("Amlodipine 5mg", "AML-2402", 15, 26, "Hypertension outpatient clinic"),
        ("Amlodipine 5mg", "AML-2402", 15, 12, "Hypertension outpatient clinic"),
        ("Amlodipine 5mg", "AML-2402", 10, 4, "Cardiology consults"),
        # Azithromycin: rapid consumption (~1.5/day), only 4 left -> predicts severe shortage!
        ("Azithromycin 250mg", "AZI-2401", 8, 24, "Chest infection clinic"),
        ("Azithromycin 250mg", "AZI-2401", 10, 14, "Severe bronchitis cohort"),
        ("Azithromycin 250mg", "AZI-2401", 8, 5, "Community clinic"),
        # Cetirizine: seasonal allergy usage
        ("Cetirizine 10mg", "CET-2401", 8, 21, "Allergy department"),
        ("Cetirizine 10mg", "CET-2401", 12, 7, "Skin allergy cases"),
        # Salbutamol: asthma emergencies
        ("Salbutamol 100mcg", "SALB-2401", 5, 20, "Emergency asthma nebulization"),
        ("Salbutamol 100mcg", "SALB-2401", 4, 6, "Pediatric wheeze emergency"),
        ("Salbutamol 100mcg", "SALB-2401", 3, 1, "Acute respiratory care"),
        # Ibuprofen
        ("Ibuprofen 400mg", "IBU-2402", 10, 19, "Orthopedic & sprain cases"),
        ("Ibuprofen 400mg", "IBU-2402", 15, 8, "Dental toothache clinic"),
        # Atorvastatin
        ("Atorvastatin 20mg", "ATOR-2401", 10, 16, "Lipid profile follow-up")
    ]

    for med_name, batch_no, qty, days_ago, reason in consumption_records:
        med_id = med_id_map.get(med_name)
        batch_id = batch_id_map.get(batch_no)
        disp_date = (today - timedelta(days=days_ago)).isoformat()
        cursor.execute("""
            INSERT INTO consumption_logs (medicine_id, batch_id, quantity, dispensed_to, dispensed_date)
            VALUES (?, ?, ?, ?, ?)
        """, (med_id, batch_id, qty, reason, disp_date))

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    init_db()
    seed_sample_data(force=True)
    print("Database initialized and sample data seeded successfully.")
