from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("visiteurs.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS visiteurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            langue TEXT,
            navigateur TEXT,
            appareil TEXT,
            fuseau TEXT,
            date_access TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route('/save', methods=['POST'])
def save_visitor():
    data = request.json
    ip = request.remote_addr
    langue = data.get('language', 'unknown')
    agent = data.get('userAgent', 'unknown')
    os = data.get('platform', 'unknown')
    fuseau = data.get('timezone', 'unknown')
    date_access = data.get('date', datetime.utcnow().isoformat())
    conn = sqlite3.connect("visiteurs.db")
    c = conn.cursor()
    c.execute("INSERT INTO visiteurs (ip, langue, navigateur, appareil, fuseau, date_access) VALUES (?, ?, ?, ?, ?, ?)",
              (ip, langue, agent, os, fuseau, date_access))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/export-json', methods=['GET'])
def export_json():
    conn = sqlite3.connect("visiteurs.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM visiteurs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    data = [dict(row) for row in rows]
    return jsonify(data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
