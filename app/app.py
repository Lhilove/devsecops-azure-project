from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def get_db():
    return sqlite3.connect("users.db")

@app.route("/")
def home():
    return "DevSecOps Demo App Running"

# Vulnerable login (SQL Injection)
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db()
    cursor = conn.cursor()

    # INTENTIONALLY VULNERABLE
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Invalid credentials"}), 401
@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()

    # No authentication or authorization check
    cursor.execute(f"SELECT id, username, password FROM users WHERE id={user_id}")
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "id": user[0],
            "username": user[1],
            "password": user[2]  # Sensitive exposure too
        })
    else:
        return jsonify({"error": "User not found"}), 404

@app.route("/ping", methods=["GET"])
def ping():
    ip = request.args.get("ip")

    # INTENTIONALLY VULNERABLE
    result = os.popen(f"ping -c 1 {ip}").read()

    return jsonify({"result": result})
@app.route("/config", methods=["GET"])
def config():
    return jsonify({
        "db_password": "supersecret123",
        "api_key": "12345-SECRET-KEY",
        "debug": True
    })

@app.route("/admin")
def admin():
    role = request.args.get("role")

    # Weak auth logic
    if role == "admin":
        return "Welcome admin!"
    else:
        return "Access denied", 403
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)