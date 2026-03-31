from flask import Flask, request, jsonify
import sqlite3
import os
import subprocess
import re

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
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Invalid credentials"}), 401


# SECURE USER FETCH (Fix IDOR + Sensitive Data Exposure)
@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    token = request.headers.get("Authorization")

    # Basic auth check (replace with JWT in real systems)
    if token != os.getenv("USER_TOKEN"):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    # Parameterized query
    cursor.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
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

    # Strict input validation (only allow digits + dots)
    if not re.match(r"^[0-9.]+$", ip):
        return jsonify({"error": "Invalid IP"}), 400

    # Safe subprocess execution (no shell)
    result = subprocess.run(
        ["ping", "-c", "1", ip],
        capture_output=True,
        text=True
    )

    return jsonify({"result": result.stdout})


# SECURE CONFIG (Remove secrets exposure)
@app.route("/config", methods=["GET"])
def config():
    return jsonify({
        "status": "OK"
    })


# SECURE ADMIN (Fix Broken Access Control)
@app.route("/admin")
def admin():
    token = request.headers.get("Authorization")

    # Role-based validation
    if token == os.getenv("ADMIN_TOKEN"):
        return "Welcome admin!"

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
    app.run(host="0.0.0.0", port=5000, debug=False)