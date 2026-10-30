"""
test_app.py - Automated verification tests for MediTrack system
Tests database operations, API endpoints, expiry calculations,
and the critical rule: 'Never count expired batches as usable stock'.
"""

import unittest
import json
from datetime import date, timedelta
from app import app
from database import init_db, seed_sample_data, get_db_connection

class MediTrackTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Re-initialize clean test data
        init_db()
        seed_sample_data(force=True)

    def test_health_check(self):
        """Test system health check endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["app"], "MediTrack")

    def test_get_medicines(self):
        """Test retrieving medicines list."""
        response = self.client.get("/api/medicines")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["medicines"]), 0)

        # Check fields
        med = data["medicines"][0]
        self.assertIn("usable_stock", med)
        self.assertIn("expired_stock", med)
        self.assertIn("stock_status", med)

    def test_expired_batches_excluded_from_usable_stock(self):
        """
        CRITICAL CLINICAL REQUIREMENT:
        Never count expired batches as usable stock!
        """
        today = date.today()
        # Find Ciprofloxacin 500mg, which in seed data only has an expired batch (CIPRO-2308)
        response = self.client.get("/api/medicines")
        data = response.get_json()
        cipro = next((m for m in data["medicines"] if "Ciprofloxacin" in m["name"]), None)
        self.assertIsNotNone(cipro)

        # Usable stock must be 0 because its batch is expired
        self.assertEqual(cipro["usable_stock"], 0, "Expired batch must NOT count towards usable stock!")
        self.assertGreater(cipro["expired_stock"], 0, "Expired quantity must be recorded as expired stock.")
        self.assertEqual(cipro["stock_status"], "OUT_OF_STOCK")

    def test_add_and_update_medicine(self):
        """Test adding and updating a medicine."""
        # 1. Add
        new_med = {
            "name": "Vitamin C 500mg Chewable",
            "category": "Supplements",
            "unit": "Tablets",
            "min_stock": 25,
            "description": "Daily immunity supplement"
        }
        res = self.client.post("/api/medicines", json=new_med)
        self.assertEqual(res.status_code, 201)
        med_id = res.get_json()["id"]

        # 2. Update
        update_data = {
            "name": "Vitamin C 500mg (Orange)",
            "category": "Supplements",
            "unit": "Tablets",
            "min_stock": 30,
            "description": "Updated flavor"
        }
        res_up = self.client.put(f"/api/medicines/{med_id}", json=update_data)
        self.assertEqual(res_up.status_code, 200)

        # Verify
        res_get = self.client.get(f"/api/medicines/{med_id}")
        self.assertEqual(res_get.get_json()["medicine"]["name"], "Vitamin C 500mg (Orange)")

    def test_batch_addition_and_expiry_categorization(self):
        """Test adding a batch and verifying expiry calculation."""
        today = date.today()
        # Add medicine first
        med_res = self.client.post("/api/medicines", json={
            "name": "Doxycycline 100mg",
            "category": "Antibiotic",
            "unit": "Capsules",
            "min_stock": 20
        })
        med_id = med_res.get_json()["id"]

        # Add batch expiring in 10 days (Expiring soon)
        exp_date = (today + timedelta(days=10)).isoformat()
        batch_res = self.client.post("/api/batches", json={
            "medicine_id": med_id,
            "batch_number": "DOXY-TEST-01",
            "quantity": 50,
            "expiry_date": exp_date,
            "supplier": "Test Supplier"
        })
        self.assertEqual(batch_res.status_code, 201)

        # Check alerts
        alert_res = self.client.get("/api/alerts/expiry")
        alert_data = alert_res.get_json()
        doxy_alert = next((b for b in alert_data["expiring_soon"] if b["batch_number"] == "DOXY-TEST-01"), None)
        self.assertIsNotNone(doxy_alert)
        self.assertEqual(doxy_alert["status"], "EXPIRING_SOON")
        self.assertEqual(doxy_alert["days_remaining"], 10)

    def test_shortage_prediction_calculation(self):
        """Test daily consumption calculation and days until stockout prediction."""
        res = self.client.get("/api/analytics/predictions")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("predictions", data)

        # Verify Azithromycin (low usable stock + active consumption -> critical shortage)
        azi = next((p for p in data["predictions"] if "Azithromycin" in p["name"]), None)
        self.assertIsNotNone(azi)
        self.assertGreater(azi["avg_daily_usage"], 0)
        self.assertLessEqual(azi["days_remaining"], 7)
        self.assertEqual(azi["risk"], "CRITICAL_SHORTAGE")

    def test_dispense_fefo_and_prevent_expired_dispense(self):
        """Test that dispensing deducts from earliest expiring batch and rejects expired batches."""
        # Find Paracetamol
        res = self.client.get("/api/medicines")
        para = next((m for m in res.get_json()["medicines"] if "Paracetamol" in m["name"]), None)
        initial_usable = para["usable_stock"]

        # Dispense 10 units
        disp_res = self.client.post("/api/consumption", json={
            "medicine_id": para["id"],
            "quantity": 10,
            "dispensed_to": "Ward A",
            "dispensed_date": date.today().isoformat()
        })
        self.assertEqual(disp_res.status_code, 200)

        # Verify usable stock decreased by 10
        res_after = self.client.get("/api/medicines")
        para_after = next((m for m in res_after.get_json()["medicines"] if "Paracetamol" in m["name"]), None)
        self.assertEqual(para_after["usable_stock"], initial_usable - 10)

        # Test dispensing Ciprofloxacin (only has expired batch)
        cipro = next((m for m in res.get_json()["medicines"] if "Ciprofloxacin" in m["name"]), None)
        disp_fail = self.client.post("/api/consumption", json={
            "medicine_id": cipro["id"],
            "quantity": 2,
            "dispensed_to": "Ward B"
        })
        self.assertEqual(disp_fail.status_code, 400)
        self.assertIn("No non-expired", disp_fail.get_json()["error"])

if __name__ == "__main__":
    unittest.main()
