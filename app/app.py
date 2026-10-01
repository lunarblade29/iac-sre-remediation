import os
import sys
from flask import Flask, jsonify

app = Flask(__name__)

# Simulates runtime memory corruption / deadlock / unhandled bug
CRASH_STATE = False

@app.route("/")
def index():
    return jsonify({"status": "healthy", "service": "orders-api", "version": "v1.0.0"}), 200

@app.route("/api/data")
def get_data():
    global CRASH_STATE
    if CRASH_STATE:
        # 503 Service Unavailable / 500 Internal Error
        return jsonify({"error": "Worker deadlock: database connection pool exhausted"}), 503
    return jsonify({"message": "Data retrieved successfully", "records": 42}), 200

# Outage trigger (mimics a poison-pill payload or memory leak triggered in production)
@app.route("/chaos/inject-bug", methods=["POST"])
def inject_bug():
    global CRASH_STATE
    CRASH_STATE = True
    app.logger.error("CRITICAL: Outage injected. Service entered degraded state.")
    return jsonify({"alert": "Poison pill received. Worker is now failing all requests."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))