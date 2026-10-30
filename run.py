"""
run.py - MediTrack Application Launcher
Starts the local development server for the MediTrack clinic management system.
"""

import sys
import os

# Ensure current directory is in python search path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from database import init_db, seed_sample_data
from app import app

def main():
    print("=" * 65)
    print("  MediTrack – Smart Medicine Inventory Monitoring System")
    print("=" * 65)
    print("[1/2] Initializing SQLite database and verifying sample records...")
    init_db()
    seed_sample_data(force=False)
    print("[2/2] Starting Flask web server on http://127.0.0.1:5000")
    print("      Open your web browser and navigate to: http://127.0.0.1:5000")
    print("      Press Ctrl+C to stop the server.")
    print("=" * 65)
    app.run(host="127.0.0.1", port=5000, debug=True)

if __name__ == "__main__":
    main()
