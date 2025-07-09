from flask import Flask, request, jsonify, abort, Response, render_template_string
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
from pydantic import BaseModel, ValidationError, constr, validator
import logging
from logging.handlers import RotatingFileHandler
import re

app = Flask(__name__)
CORS(app)

DB_PATH = "visiteurs.db"
db_lock = Lock()

# Logger setup
logger = logging.getLogger('serveur')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('serveur.log', maxBytes=5_000_000, backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Pydantic model
class VisitorData(BaseModel):
    language: constr(strip_whitespace=True, min_length=2, max_length=20)
    userAgent: constr(strip_whitespace=True, min_length=5, max_length=500)
    platform: constr(strip_whitespace=True, min_length=2, max_length=50)
    timezone: constr(strip_whitespace=True, min_length=2, max_length=100)
    date: constr(strip_whitespace=True, min_length=10, max_length=40)
    ip: constr(strip_whitespace=True, min_length=7, max_length=45)

    @validator("timezone")
    def validate_timezone(cls, v):
        if not re.match(r"^[\w\/\-\+]+$", v):
            raise ValueError("Timezone invalide")
        return v

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_lock:
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS visiteurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                langue TEXT,
                navigateur TEXT,
                appareil TEXT,
                fuseau TEXT,
                date_access TEXT
            )
        ''')
        conn.commit()
        conn.close()
    logger.info("Base de données initialisée")

# Rate limiting (simple)
RATE_LIMIT = 100
RATE_PERIOD = 60
visitors_requests = {}
requests_lock = Lock()

def is_rate_limited(ip):
    now = int(datetime.now().timestamp())
    with requests_lock:
        times = visitors_requests.get(ip, [])
        times = [t for t in times if now - t < RATE_PERIOD]
        if len(times) >= RATE_LIMIT:
            return True
        times.append(now)
        visitors_requests[ip] = times
    return False

def build_filter_query(params):
    filters = []
    values = []
    if 'ip' in params:
        filters.append("ip LIKE ?")
        values.append(f"%{params['ip']}%")
    if 'langue' in params:
        filters.append("langue LIKE ?")
        values.append(f"%{params['langue']}%")
    if 'navigateur' in params:
        filters.append("navigateur LIKE ?")
        values.append(f"%{params['navigateur']}%")
    if 'appareil' in params:
        filters.append("appareil LIKE ?")
        values.append(f"%{params['appareil']}%")
    if 'fuseau' in params:
        filters.append("fuseau LIKE ?")
        values.append(f"%{params['fuseau']}%")
    where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""
    return where_clause, values

@app.route("/")
def home():
    return render_template_string("""
    <html><body>
    <h1>Serveur Visiteurs</h1>
    <ul>
      <li><a href="/admin">/admin</a></li>
      <li><a href="/export-json">/export-json</a></li>
      <li><a href="/export-csv">/export-csv</a></li>
      <li><a href="/stats">/stats</a></li>
      <li><a href="/health">/health</a></li>
      <li><a href="/docs">/docs</a></li>
    </ul>
    </body></html>
    """)

@app.route("/save", methods=["POST"])
def save_visitor():
    ip = request.remote_addr or "0.0.0.0"
    if is_rate_limited(ip):
        return jsonify({"error": "Trop de requêtes, réessayez plus tard."}), 429

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Requête JSON invalide"}), 400

    if data is None:
        return jsonify({"error": "Données manquantes"}), 400

    data['ip'] = ip
    try:
        visitor = VisitorData(**data)
    except ValidationError as e:
        return jsonify({"error": "Données invalides", "details": e.errors()}), 422

    with db_lock:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO visiteurs (ip, langue, navigateur, appareil, fuseau, date_access) VALUES (?, ?, ?, ?, ?, ?)",
            (visitor.ip, visitor.language, visitor.userAgent, visitor.platform, visitor.timezone, visitor.date)
        )
        conn.commit()
        conn.close()

    return jsonify({"success": True}), 201

@app.route("/admin")
def admin_page():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(max(per_page, 1), 100)

    sort_by = request.args.get("sort_by", "date_access")
    order = request.args.get("order", "desc")
    valid_sort = {"date_access", "ip", "langue", "navigateur", "appareil", "fuseau", "id"}
    if sort_by not in valid_sort:
        sort_by = "date_access"
    order = "ASC" if order.lower() == "asc" else "DESC"

    filters = {k: request.args.get(k) for k in ["ip", "langue", "navigateur", "appareil", "fuseau"] if request.args.get(k)}

    where_clause, values = build_filter_query(filters)

    with db_lock:
        conn = get_db_connection()
        count_res = conn.execute(f"SELECT COUNT(*) as total FROM visiteurs {where_clause}", values).fetchone()
        total = count_res["total"] if count_res else 0
        offset = (page - 1) * per_page

        query = f"""
            SELECT * FROM visiteurs
            {where_clause}
            ORDER BY {sort_by} {order}
            LIMIT ? OFFSET ?
        """
        cur = conn.execute(query, (*values, per_page, offset))
        visiteurs = cur.fetchall()
        conn.close()

    total_pages = max(1, (total + per_page - 1) // per_page)

    html = f"""
    <html><head><title>Admin Visiteurs</title>
    <style>
      body {{ font-family: Arial, sans-serif; background:#121212; color:#eee; margin:0; padding:20px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
      th, td {{ padding: 10px; border: 1px solid #444; }}
      th {{ background-color: #ff6f61; cursor:pointer; }}
      tr:nth-child(even) {{ background-color: #1e1e1e; }}
      tr:hover {{ background-color: #333; }}
      a {{ color:#ff6f61; text-decoration:none; }}
      a:hover {{ text-decoration:underline; }}
      .pagination {{ margin-top: 15px; text-align:center; }}
      form input {{ padding: 5px; margin-right: 8px; background: #222; border: 1px solid #444; color: #eee; border-radius: 3px; }}
      form button {{ background: #ff6f61; border:none; color:#fff; padding: 6px 10px; cursor:pointer; border-radius:3px; }}
    </style>
    </head><body>
    <h1>Visiteurs (page {page}/{total_pages})</h1>
    <form method="get" action="/admin">
      <input name="ip" placeholder="Filtrer IP" value="{filters.get('ip', '')}"/>
      <input name="langue" placeholder="Filtrer langue" value="{filters.get('langue', '')}"/>
      <input name="navigateur" placeholder="Filtrer navigateur" value="{filters.get('navigateur', '')}"/>
      <input name="appareil" placeholder="Filtrer appareil" value="{filters.get('appareil', '')}"/>
      <input name="fuseau" placeholder="Filtrer fuseau" value="{filters.get('fuseau', '')}"/>
      <input type="hidden" name="sort_by" value="{sort_by}"/>
      <input type="hidden" name="order" value="{order}"/>
      <input type="hidden" name="per_page" value="{per_page}"/>
      <button type="submit">Filtrer</button>
    </form>
    <table>
      <thead>
        <tr>
          <th><a href="/admin?sort_by=id&order={'asc' if sort_by != 'id' or order == 'desc' else 'desc'}&page=1">ID</a></th>
          <th><a href="/admin?sort_by=ip&order={'asc' if sort_by != 'ip' or order == 'desc' else 'desc'}&page=1">IP</a></th>
          <th><a href="/admin?sort_by=langue&order={'asc' if sort_by != 'langue' or order == 'desc' else 'desc'}&page=1">Langue</a></th>
          <th><a href="/admin?sort_by=navigateur&order={'asc' if sort_by != 'navigateur' or order == 'desc' else 'desc'}&page=1">Navigateur</a></th>
          <th><a href="/admin?sort_by=appareil&order={'asc' if sort_by != 'appareil' or order == 'desc' else 'desc'}&page=1">Appareil</a></th>
          <th><a href="/admin?sort_by=fuseau&order={'asc' if sort_by != 'fuseau' or order == 'desc' else 'desc'}&page=1">Fuseau</a></th>
          <th><a href="/admin?sort_by=date_access&order={'asc' if sort_by != 'date_access' or order == 'desc' else 'desc'}&page=1">Date</a></th>
        </tr>
      </thead><tbody>
    """
    for v in visiteurs:
        html += f"<tr><td>{v['id']}</td><td>{v['ip']}</td><td>{v['langue']}</td><td>{v['navigateur']}</td><td>{v['appareil']}</td><td>{v['fuseau']}</td><td>{v['date_access']}</td></tr>"
    html += "</tbody></table><div class='pagination'>"
    if page > 1:
        html += f'<a href="/admin?page={page-1}&per_page={per_page}&sort_by={sort_by}&order={order}">&laquo; Page précédente</a>'
    if page < total_pages:
        html += f'<a href="/admin?page={page+1}&per_page={per_page}&sort_by={sort_by}&order={order}">Page suivante &raquo;</a>'
    html += "</div></body></html>"
    return html

@app.route("/visiteurs")
def visiteurs_json():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(max(per_page, 1), 100)

    sort_by = request.args.get("sort_by", "date_access")
    order = request.args.get("order", "desc")
    valid_sort = {"date_access", "ip", "langue", "navigateur", "appareil", "fuseau", "id"}
    if sort_by not in valid_sort:
        sort_by = "date_access"
    order = "ASC" if order.lower() == "asc" else "DESC"

    filters = {k: request.args.get(k) for k in ["ip", "langue", "navigateur", "appareil", "fuseau"] if request.args.get(k)}

    where_clause, values = build_filter_query(filters)

    with db_lock:
        conn = get_db_connection()
        count_res = conn.execute(f"SELECT COUNT(*) as total FROM visiteurs {where_clause}", values).fetchone()
        total = count_res["total"] if count_res else 0
        offset = (page - 1) * per_page

        query = f"""
            SELECT * FROM visiteurs
            {where_clause}
            ORDER BY {sort_by} {order}
            LIMIT ? OFFSET ?
        """
        cur = conn.execute(query, (*values, per_page, offset))
        visiteurs = cur.fetchall()
        conn.close()

    total_pages = max(1, (total + per_page - 1) // per_page)
    visiteurs_list = [dict(v) for v in visiteurs]
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "data": visiteurs_list
    })

@app.route("/visiteurs/<int:id>")
def visiteurs_detail(id):
    with db_lock:
        conn = get_db_connection()
        visiteur = conn.execute("SELECT * FROM visiteurs WHERE id = ?", (id,)).fetchone()
        conn.close()
    if visiteur is None:
        abort(404, description="Visiteur non trouvé")
    return jsonify(dict(visiteur))

@app.route("/clear-db", methods=["POST"])
def clear_db():
    with db_lock:
        conn = get_db_connection()
        conn.execute("DELETE FROM visiteurs")
        conn.commit()
        conn.close()
    logger.warning("Base de données vidée manuellement")
    return jsonify({"success": True, "message": "Base de données vidée"})

@app.route("/export-json")
def export_json():
    with db_lock:
        conn = get_db_connection()
        visiteurs = conn.execute("SELECT * FROM visiteurs ORDER BY date_access DESC").fetchall()
        conn.close()
    data = [dict(v) for v in visiteurs]
    return jsonify(data)

@app.route("/export-csv")
def export_csv():
    import csv
    from io import StringIO

    with db_lock:
        conn = get_db_connection()
        visiteurs = conn.execute("SELECT * FROM visiteurs ORDER BY date_access DESC").fetchall()
        conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(visiteurs[0].keys() if visiteurs else ["id", "ip", "langue", "navigateur", "appareil", "fuseau", "date_access"])
    for v in visiteurs:
        cw.writerow(v)
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=visiteurs.csv"})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

@app.route("/stats")
def stats():
    with db_lock:
        conn = get_db_connection()
        total_visitors = conn.execute("SELECT COUNT(DISTINCT ip) FROM visiteurs").fetchone()[0]
        total_visits = conn.execute("SELECT COUNT(*) FROM visiteurs").fetchone()[0]

        one_month_ago = datetime.utcnow() - timedelta(days=30)
        visits_per_day = conn.execute("""
            SELECT substr(date_access,1,10) as day, COUNT(*) FROM visiteurs 
            WHERE date_access >= ? GROUP BY day ORDER BY day DESC
        """, (one_month_ago.isoformat(),)).fetchall()
        conn.close()

    return jsonify({
        "total_visitors_unique": total_visitors,
        "total_visits": total_visits,
        "visits_per_day_last_30d": [{row[0]: row[1]} for row in visits_per_day]
    })

@app.route("/docs")
def docs():
    return render_template_string("""
    <html><head><title>Docs API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: auto; padding: 20px; background: #121212; color: #eee; }
        h1,h2 { color: #ff6f61; }
        code { background: #222; padding: 2px 5px; border-radius: 3px; }
        pre { background: #222; padding: 10px; border-radius: 5px; overflow-x: auto; }
        a { color: #ff6f61; text-decoration: none; }
        a:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; border: 1px solid #444; }
        th { background-color: #ff6f61; color: white; }
    </style>
    </head><body>
    <h1>Documentation API Visiteurs</h1>
    <p>Ce serveur collecte et affiche les données visiteurs.</p>
    <h2>POST /save</h2>
    <p>Envoie un JSON avec :</p>
    <pre>{
  "language": "fr",
  "userAgent": "Mozilla/5.0 ...",
  "platform": "Windows",
  "timezone": "Europe/Paris",
  "date": "2025-07-09T16:00:00Z"
}</pre>
    <p>L'IP est automatiquement prise en compte par le serveur.</p>
    <h2>GET /admin</h2>
    <p>Page web paginée affichant les visiteurs. Paramètres :</p>
    <ul>
      <li><code>page</code> - numéro de page (défaut 1)</li>
      <li><code>per_page</code> - nombre par page (max 100)</li>
      <li><code>sort_by</code> - champ de tri (id, ip, langue, navigateur, appareil, fuseau, date_access)</li>
      <li><code>order</code> - asc ou desc</li>
      <li><code>ip, langue, navigateur, appareil, fuseau</code> - filtres (recherche)</li>
    </ul>
    <h2>GET /visiteurs</h2>
    <p>Liste JSON paginée avec mêmes paramètres que /admin</p>
    <h2>GET /visiteurs/&lt;id&gt;</h2>
    <p>Détail d’un visiteur par ID</p>
    <h2>GET /export-json</h2>
    <p>Export complet en JSON</p>
    <h2>GET /export-csv</h2>
    <p>Export complet en CSV</p>
    <h2>GET /health</h2>
    <p>Status du serveur (ping)</p>
    <h2>GET /stats</h2>
    <p>Statistiques simples</p>
    </body></html>
    """)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
