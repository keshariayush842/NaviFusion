from flask import Flask, jsonify, send_from_directory
import csv
import os
from collections import deque

app = Flask(__name__)

BASE_DIR = os.path.expanduser("~/navifusion_ws")
CSV_FILE = os.path.join(BASE_DIR, "live_telemetry.csv")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")


def read_telemetry(limit=300):
    rows = []

    if not os.path.exists(CSV_FILE):
        return rows

    try:
        with open(CSV_FILE, "r", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    row["timestamp"] = float(row["timestamp"])
                    row["ekf_x"] = float(row["ekf_x"])
                    row["ekf_y"] = float(row["ekf_y"])
                    row["imu_x"] = float(row["imu_x"])
                    row["imu_y"] = float(row["imu_y"])
                    row["drift_error"] = float(row["drift_error"])
                    row["gnss_mahalanobis"] = float(row["gnss_mahalanobis"])
                    row["anomaly_count"] = int(float(row["anomaly_count"]))
                    row["navigation_confidence"] = float(row["navigation_confidence"])
                    row["intelligence_score"] = float(row["intelligence_score"])
                except (ValueError, TypeError):
                    continue

                rows.append(row)

    except Exception as e:
        print("CSV read error:", e)

    return rows[-limit:]


@app.route("/")
def index():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/api/data")
def api_data():
    rows = read_telemetry(400)

    latest = rows[-1] if rows else {}

    return jsonify({
        "latest": latest,
        "history": rows
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "csv_exists": os.path.exists(CSV_FILE),
        "csv_size": os.path.getsize(CSV_FILE) if os.path.exists(CSV_FILE) else 0
    })


if __name__ == "__main__":
    print("")
    print("==============================================")
    print("        NAVIFUSION DASHBOARD ONLINE")
    print("==============================================")
    print("Telemetry:", CSV_FILE)
    print("Dashboard: http://localhost:5000")
    print("==============================================")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
