import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import csv
from datetime import datetime, timedelta
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from flask import Flask, request, jsonify
from flask_cors import CORS

DB_PATH = "visiteurs.db"

# === DB Functions (identiques à ton code) ===

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
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

def get_visiteurs(filters=None, order_by="date_access DESC", limit=None, offset=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = "SELECT * FROM visiteurs"
    params = []
    if filters:
        where_clauses = []
        for k,v in filters.items():
            if v:
                where_clauses.append(f"{k} LIKE ?")
                params.append(f"%{v}%")
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
    query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def count_visiteurs(filters=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT COUNT(*) FROM visiteurs"
    params = []
    if filters:
        where_clauses = []
        for k,v in filters.items():
            if v:
                where_clauses.append(f"{k} LIKE ?")
                params.append(f"%{v}%")
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
    c.execute(query, params)
    count = c.fetchone()[0]
    conn.close()
    return count

def add_visiteur(ip, langue, navigateur, appareil, fuseau, date_access):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO visiteurs (ip, langue, navigateur, appareil, fuseau, date_access) VALUES (?, ?, ?, ?, ?, ?)",
              (ip, langue, navigateur, appareil, fuseau, date_access))
    conn.commit()
    conn.close()

def delete_visiteur(visitor_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM visiteurs WHERE id = ?", (visitor_id,))
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM visiteurs")
    conn.commit()
    conn.close()

# === Flask Server ===

app = Flask(__name__)
CORS(app, origins=["https://noctavia.github.io/Prank/"])

@app.route("/save", methods=["POST"])
def save_visitor():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    ip = request.remote_addr or "0.0.0.0"
    langue = data.get("langue", "")
    navigateur = data.get("navigateur", "")
    appareil = data.get("appareil", "")
    fuseau = data.get("fuseau", "")
    date_access = data.get("date_access", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    add_visiteur(ip, langue, navigateur, appareil, fuseau, date_access)

    print(f"[Flask] Visiteur ajouté: IP={ip} Langue={langue}")
    return jsonify({"success": True})

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# === Tkinter GUI ===

class VisitorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion Visiteurs - Avancé")
        self.geometry("1100x700")

        self.filters = {
            "ip": tk.StringVar(),
            "langue": tk.StringVar(),
            "navigateur": tk.StringVar(),
            "appareil": tk.StringVar(),
            "fuseau": tk.StringVar(),
            "date_access": tk.StringVar()
        }
        self.sort_col = "date_access"
        self.sort_dir = "DESC"
        self.page = 1
        self.per_page = 25
        self.total_count = 0

        self.create_widgets()
        self.load_data()

        # Démarrer serveur Flask en thread
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()

    # (tout le reste identique à ton code GUI, coller ici...)

    def create_widgets(self):
        # --- Filtres Frame ---
        filter_frame = ttk.LabelFrame(self, text="Filtres")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        for i,(key,var) in enumerate(self.filters.items()):
            ttk.Label(filter_frame, text=key.capitalize()).grid(row=0, column=i, padx=5)
            ttk.Entry(filter_frame, textvariable=var, width=15).grid(row=1, column=i, padx=5)
        ttk.Button(filter_frame, text="Rechercher", command=self.search).grid(row=1, column=len(self.filters), padx=10)
        ttk.Button(filter_frame, text="Effacer", command=self.clear_filters).grid(row=1, column=len(self.filters)+1, padx=10)

        # --- Table ---
        cols = ("id", "ip", "langue", "navigateur", "appareil", "fuseau", "date_access")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for c in cols:
            self.tree.heading(c, text=c.capitalize(), command=lambda _c=c: self.sort_by_column(_c))
            self.tree.column(c, anchor=tk.W, width=140 if c != "id" else 50)

        self.tree.bind("<Double-1>", self.on_row_double_click)

        # --- Pagination ---
        pag_frame = ttk.Frame(self)
        pag_frame.pack(fill=tk.X, padx=10, pady=5)
        self.page_label = ttk.Label(pag_frame, text="Page 1")
        self.page_label.pack(side=tk.LEFT)
        ttk.Button(pag_frame, text="<< Précédent", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(pag_frame, text="Suivant >>", command=self.next_page).pack(side=tk.LEFT, padx=5)

        # --- Buttons ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Ajouter visiteur test", command=self.add_sample).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ajouter visiteur manuel", command=self.add_manual).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer sélection", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Vider base", command=self.clear_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter JSON (filtré)", command=self.export_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter CSV (filtré)", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Voir stats", command=self.show_stats).pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def load_data(self):
        filters = {k: v.get() for k,v in self.filters.items() if v.get()}
        order_by = f"{self.sort_col} {self.sort_dir}"
        offset = (self.page -1) * self.per_page
        data = get_visiteurs(filters=filters, order_by=order_by, limit=self.per_page, offset=offset)
        self.total_count = count_visiteurs(filters=filters)

        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in data:
            self.tree.insert("", "end", values=row)

        total_pages = max(1, (self.total_count + self.per_page -1)//self.per_page)
        self.page_label.config(text=f"Page {self.page} / {total_pages}")
        self.status_var.set(f"Total visiteurs (filtrés) : {self.total_count}")

    def search(self):
        self.page = 1
        self.load_data()

    def clear_filters(self):
        for v in self.filters.values():
            v.set("")
        self.page = 1
        self.load_data()

    def sort_by_column(self, col):
        if self.sort_col == col:
            self.sort_dir = "ASC" if self.sort_dir == "DESC" else "DESC"
        else:
            self.sort_col = col
            self.sort_dir = "ASC"
        self.load_data()

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_data()

    def next_page(self):
        total_pages = max(1, (self.total_count + self.per_page -1)//self.per_page)
        if self.page < total_pages:
            self.page += 1
            self.load_data()

    def add_sample(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_visiteur("192.168.1.1", "fr-FR", "Chrome", "PC", "Europe/Paris", now)
        self.load_data()
        messagebox.showinfo("Ajout", "Visiteur test ajouté")

    def add_manual(self):
        def save_manual():
            ip = ip_var.get()
            langue = langue_var.get()
            nav = nav_var.get()
            appareil = app_var.get()
            fuseau = fuseau_var.get()
            date_access = date_var.get()

            if not ip or not date_access:
                messagebox.showerror("Erreur", "IP et Date sont obligatoires")
                return

            try:
                datetime.strptime(date_access, "%Y-%m-%d %H:%M:%S")
            except:
                messagebox.showerror("Erreur", "Date invalide (format: YYYY-MM-DD HH:MM:SS)")
                return

            add_visiteur(ip, langue, nav, appareil, fuseau, date_access)
            self.load_data()
            top.destroy()
            messagebox.showinfo("Ajout", "Visiteur ajouté manuellement")

        top = tk.Toplevel(self)
        top.title("Ajouter visiteur manuel")

        ip_var = tk.StringVar()
        langue_var = tk.StringVar()
        nav_var = tk.StringVar()
        app_var = tk.StringVar()
        fuseau_var = tk.StringVar()
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        labels = ["IP", "Langue", "Navigateur", "Appareil", "Fuseau", "Date (YYYY-MM-DD HH:MM:SS)"]
        vars_ = [ip_var, langue_var, nav_var, app_var, fuseau_var, date_var]

        for i, (label, var) in enumerate(zip(labels, vars_)):
            ttk.Label(top, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Entry(top, textvariable=var, width=30).grid(row=i, column=1, padx=5, pady=3)

        ttk.Button(top, text="Ajouter", command=save_manual).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Avertissement", "Aucune sélection")
            return
        if messagebox.askyesno("Confirmer", "Supprimer les visiteurs sélectionnés ?"):
            for sel in selected:
                visitor_id = self.tree.item(sel)["values"][0]
                delete_visiteur(visitor_id)
            self.load_data()

    def clear_database(self):
        if messagebox.askyesno("Confirmer", "Vider complètement la base de données ?"):
            clear_db()
            self.load_data()

    def export_json(self):
        filters = {k: v.get() for k,v in self.filters.items() if v.get()}
        data = get_visiteurs(filters=filters, order_by=f"{self.sort_col} {self.sort_dir}")
        visiteurs = []
        for row in data:
            visiteurs.append({
                "id": row[0], "ip": row[1], "langue": row[2],
                "navigateur": row[3], "appareil": row[4], "fuseau": row[5], "date_access": row[6]
            })
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(visiteurs, f, indent=4)
            messagebox.showinfo("Succès", f"Export JSON sauvegardé : {filepath}")

    def export_csv(self):
        filters = {k: v.get() for k,v in self.filters.items() if v.get()}
        data = get_visiteurs(filters=filters, order_by=f"{self.sort_col} {self.sort_dir}")
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if filepath:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "ip", "langue", "navigateur", "appareil", "fuseau", "date_access"])
                for row in data:
                    writer.writerow(row)
            messagebox.showinfo("Succès", f"Export CSV sauvegardé : {filepath}")

    def show_stats(self):
        visiteurs = get_visiteurs()
        if not visiteurs:
            messagebox.showinfo("Stats", "Pas de données pour générer les statistiques.")
            return

        ips = [v[1] for v in visiteurs]
        total_visiteurs_uniques = len(set(ips))
        total_visites = len(visiteurs)

        now = datetime.now()
        one_month_ago = now - timedelta(days=30)
        visites_30j = [v for v in visiteurs if datetime.strptime(v[6], "%Y-%m-%d %H:%M:%S") >= one_month_ago]

        days = [(one_month_ago + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
        counts = Counter(datetime.strptime(v[6], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d") for v in visites_30j)
        counts_list = [counts.get(day, 0) for day in days]

        top = tk.Toplevel(self)
        top.title("Statistiques Visiteurs")
        top.geometry("800x500")

        ttk.Label(top, text=f"Visiteurs uniques : {total_visiteurs_uniques}").pack(pady=5)
        ttk.Label(top, text=f"Total visites : {total_visites}").pack(pady=5)

        fig, ax = plt.subplots(figsize=(8,3))
        ax.bar(days, counts_list, color="#ff6f61")
        ax.set_title("Visites par jour (30 derniers jours)")
        ax.set_xticks(days[::5])
        ax.set_xticklabels(days[::5], rotation=45, ha='right')
        ax.set_ylabel("Nombre de visites")

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        visitor = self.tree.item(item)["values"]
        detail = "\n".join([
            f"ID: {visitor[0]}",
            f"IP: {visitor[1]}",
            f"Langue: {visitor[2]}",
            f"Navigateur: {visitor[3]}",
            f"Appareil: {visitor[4]}",
            f"Fuseau: {visitor[5]}",
            f"Date: {visitor[6]}",
        ])
        messagebox.showinfo("Détail visiteur", detail)


if __name__ == "__main__":
    init_db()
    gui = VisitorGUI()
    gui.mainloop()
