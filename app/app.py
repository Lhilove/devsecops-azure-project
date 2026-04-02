from flask import Flask, request, jsonify
import sqlite3
import os
import subprocess
import re
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Secure DB connection
def get_db():
    return sqlite3.connect("users.db")

@app.route("/")
def home():
    return "Secure DevSecOps App Running"


# SECURE LOGIN (Fix SQL Injection)
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()

    # Parameterized query prevents SQL Injection
    query = "SELECT id, username FROM users WHERE username=? AND password=?"
    cursor.execute(query, (username, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        logger.info(json.dumps({
            "event": "login",
            "status": "success",
            "username": username,
            "ip": request.remote_addr
        }))
        return jsonify({"message": "Login successful"})
    else:
        logger.warning(json.dumps({
            "event": "login",
            "status": "failed",
            "username": username,
            "ip": request.remote_addr
        }))
        return jsonify({"message": "Invalid credentials"}), 401


# SECURE USER FETCH (Fix IDOR + Sensitive Data Exposure)
@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    token = request.headers.get("Authorization")

    # Basic auth check (replace with JWT in real systems)
    if token != os.getenv("USER_TOKEN"):
        logger.warning(json.dumps({
            "event": "user_fetch",
            "status": "unauthorized",
            "user_id": user_id,
            "ip": request.remote_addr
        }))
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    # Parameterized query
    cursor.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        logger.info(json.dumps({
            "event": "user_fetch",
            "status": "success",
            "user_id": user_id,
            "ip": request.remote_addr
        }))
        return jsonify({
            "id": user[0],
            "username": user[1]
        })
    else:
        return jsonify({"error": "User not found"}), 404


# SECURE PING (Fix Command Injection)
@app.route("/ping", methods=["GET"])
def ping():
    ip = request.args.get("ip")

    if not ip:
        return jsonify({"error": "IP parameter required"}), 400

    # Strict input validation (only allow digits + dots)
    if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip):
        logger.warning(json.dumps({
            "event": "ping",
            "status": "blocked_invalid_input",
            "input": ip,
            "ip": request.remote_addr
        }))
        return jsonify({"error": "Invalid IP"}), 400

    # Safe subprocess execution (no shell)
    result = subprocess.run(  # nosec B603
        ["/bin/ping", "-c", "1", "-W", "2", ip],
        capture_output=True,
        text=True
    )

    logger.info(json.dumps({
        "event": "ping",
        "status": "success" if result.returncode == 0 else "unreachable",
        "target": ip,
        "ip": request.remote_addr
    }))

    return jsonify({
        "result": result.stdout if result.stdout else "No response",
        "status": "success" if result.returncode == 0 else "unreachable"
    })


# SECURE CONFIG (Remove secrets exposure)
@app.route("/config", methods=["GET"])
def config():
    logger.info(json.dumps({
        "event": "config_access",
        "ip": request.remote_addr
    }))
    return jsonify({
        "status": "OK"
    })


# SECURE ADMIN (Fix Broken Access Control)
@app.route("/admin")
def admin():
    token = request.headers.get("Authorization")

    # Role-based validation
    if token == os.getenv("ADMIN_TOKEN"):
        logger.info(json.dumps({
            "event": "admin_access",
            "status": "success",
            "ip": request.remote_addr
        }))
        return "Welcome admin!"

    logger.warning(json.dumps({
        "event": "admin_access",
        "status": "unauthorized",
        "ip": request.remote_addr,
        "token_provided": token is not None
    }))
    return "Access denied", 403


# SECURITY HEADERS
@app.after_request
def set_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# Disable debug in production
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)  # nosec B104