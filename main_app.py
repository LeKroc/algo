import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import csv
import os
import hashlib
import hmac
import secrets
from datetime import datetime
import re 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# CONFIGURATION
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FILE_USERS = 'users.csv'
FILE_LOGS = 'security_logs.csv'
FILE_CMD = 'commande.csv'
API_URL = "http://127.0.0.1:5000/api"

# =============================================================================
# SÉCURITÉ LOCALE (Gestion Fichiers & Inscription)
# =============================================================================
class SecurityManager:
    @staticmethod
    def init_files():
        if not os.path.exists(FILE_USERS):
            with open(FILE_USERS, 'w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(["username", "salt", "password_hash", "role"])
        if not os.path.exists(FILE_LOGS):
            with open(FILE_LOGS, 'w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(["timestamp", "username", "status", "message"])
        if not os.path.exists(FILE_CMD):
            with open(FILE_CMD, 'w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(["id_cmd", "produit", "qte", "total", "date"])

    @staticmethod
    def check_complexity(password):
        if len(password) < 8: return False, "Min 8 caractères"
        if not re.search(r"[A-Z]", password): return False, "Manque 1 Majuscule"
        if not re.search(r"\d", password): return False, "Manque 1 Chiffre"
        if not re.search(r"[ !@#$%^&*()_+\-=\[\]{};':\\|,.<>/?]", password): return False, "Manque 1 Caractère spécial"
        return True, "OK"

    @staticmethod
    def register(username, password):
        valid, msg = SecurityManager.check_complexity(password)
        if not valid: return False, msg
        
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        
        # Attribution auto du rôle pour la démo
        role = "admin" if "admin" in username.lower() else "commercant"
        
        with open(FILE_USERS, 'a', encoding='utf-8', newline='') as f:
            csv.writer(f).writerow([username, salt, key.hex(), role])
        return True, f"Compte créé (Rôle: {role})"

    @staticmethod
    def login_local(username, password):
        if not os.path.exists(FILE_USERS): return False, "Pas d'utilisateurs"
        with open(FILE_USERS, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == username:
                    salt, stored_hash, role = row[1], row[2], row[3]
                    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
                    if hmac.compare_digest(stored_hash, key.hex()):
                        return True, role
        return False, "Echec Auth"

# =============================================================================
# INTERFACE GRAPHIQUE
# =============================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Stock Manager V4.0")
        self.geometry("1100x750")
        SecurityManager.init_files()
        
        self.current_user = None
        self.current_role = None
        self.api_token = None
        self.products_cache = []

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.show_login()

    def clear(self):
        for w in self.container.winfo_children(): w.destroy()

    # --- ECRAN LOGIN ---
    def show_login(self):
        self.clear()
        fr = ctk.CTkFrame(self.container, width=400, height=500, corner_radius=20)
        fr.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(fr, text="AUTHENTIFICATION", font=("Arial", 24, "bold")).pack(pady=30)
        self.entry_u = ctk.CTkEntry(fr, placeholder_text="Identifiant", width=250); self.entry_u.pack(pady=10)
        self.entry_p = ctk.CTkEntry(fr, placeholder_text="Mot de passe", show="*", width=250); self.entry_p.pack(pady=10)
        
        self.btn_log = ctk.CTkButton(fr, text="Connexion", width=250, command=self.do_login); self.btn_log.pack(pady=20)
        
        self.sw_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(fr, text="Mode Inscription", variable=self.sw_var, onvalue="on", offvalue="off", command=self.toggle_log).pack(pady=10)

    def toggle_log(self):
        is_reg = self.sw_var.get() == "on"
        self.btn_log.configure(text="Créer Compte" if is_reg else "Connexion", fg_color="green" if is_reg else "#1f6aa5")

    def do_login(self):
        u, p = self.entry_u.get(), self.entry_p.get()
        if self.sw_var.get() == "on":
            ok, msg = SecurityManager.register(u, p)
            messagebox.showinfo("Info", msg)
            if ok: self.sw_var.set("off"); self.toggle_log()
        else:
            ok, role = SecurityManager.login_local(u, p)
            if ok:
                self.current_user = u
                self.current_role = role
                self.connect_api(u, p)
                self.show_dash()
            else: messagebox.showerror("Erreur", "Identifiants invalides")

    def connect_api(self, u, p):
        try:
            r = requests.post(f"{API_URL}/auth/login", json={"username": u, "password": p}, timeout=1)
            if r.status_code == 200:
                self.api_token = r.json().get("token")
                print("✅ Connecté à l'API")
            else: messagebox.showwarning("API", "Mode hors-ligne (API refusée)")
        except: messagebox.showerror("Erreur", "Serveur éteint !")

    # --- DASHBOARD ---
    def show_dash(self):
        self.clear()
        
        # Sidebar
        side = ctk.CTkFrame(self.container, width=200, corner_radius=0)
        side.pack(side="left", fill="y")
        ctk.CTkLabel(side, text=f"👤 {self.current_user}", font=("Arial", 20, "bold")).pack(pady=30)
        col = "#ff5555" if self.current_role == "admin" else "#55ff55"
        ctk.CTkLabel(side, text=f"{self.current_role.upper()}", text_color=col).pack(pady=5)
        ctk.CTkButton(side, text="Déconnexion", fg_color="#cc3333", command=self.show_login).pack(side="bottom", pady=20, padx=20)

        # Onglets
        tabs = ctk.CTkTabview(self.container)
        tabs.pack(side="right", fill="both", expand=True, padx=20, pady=10)
        self.setup_stock(tabs.add("Stocks"))
        self.setup_cmd(tabs.add("Commandes"))
        self.setup_stats(tabs.add("Stats"))

    # --- ONGLETS ---
    def setup_stock(self, parent):
        fr = ctk.CTkFrame(parent); fr.pack(fill="x", pady=10)
        self.e_nom = ctk.CTkEntry(fr, placeholder_text="Nom"); self.e_nom.pack(side="left", padx=5)
        self.e_stk = ctk.CTkEntry(fr, placeholder_text="Stock", width=60); self.e_stk.pack(side="left", padx=5)
        self.e_prx = ctk.CTkEntry(fr, placeholder_text="Prix", width=60); self.e_prx.pack(side="left", padx=5)
        ctk.CTkButton(fr, text="+ Ajouter", command=self.api_add).pack(side="left", padx=10)

        if self.current_role == "admin":
            ctk.CTkButton(fr, text="Supprimer (Admin)", fg_color="#cc3333", command=self.api_del).pack(side="right", padx=10)

        cols = ("id", "nom", "stock", "prix")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        for c in cols: self.tree.heading(c, text=c.capitalize())
        self.tree.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkButton(parent, text="Actualiser", command=self.refresh_stock).pack(pady=5)
        self.refresh_stock()

    def setup_cmd(self, parent):
        fr = ctk.CTkFrame(parent); fr.pack(fill="x", pady=10)
        self.ec_id = ctk.CTkEntry(fr, placeholder_text="ID Prod", width=80); self.ec_id.pack(side="left", padx=5)
        self.ec_qt = ctk.CTkEntry(fr, placeholder_text="Qté", width=80); self.ec_qt.pack(side="left", padx=5)
        ctk.CTkButton(fr, text="Commander", fg_color="green", command=self.do_cmd).pack(side="left", padx=10)
        
        if self.current_role == "admin":
            ctk.CTkButton(fr, text="Vider Histo (Admin)", fg_color="#cc3333", command=self.clean_histo).pack(side="right", padx=10)

        self.tree_cmd = ttk.Treeview(parent, columns=("id","prod","qte","tot","date"), show="headings")
        self.tree_cmd.heading("id", text="#"); self.tree_cmd.heading("prod", text="Produit")
        self.tree_cmd.heading("qte", text="Qté"); self.tree_cmd.heading("tot", text="Total")
        self.tree_cmd.heading("date", text="Date")
        self.tree_cmd.pack(fill="both", expand=True, pady=10)
        self.load_histo()

    def setup_stats(self, parent):
        self.fr_stat = ctk.CTkFrame(parent); self.fr_stat.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkButton(parent, text="Rafraîchir", command=self.refresh_stats).pack(pady=5)

    # --- LOGIQUE ---
    def refresh_stock(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if not self.api_token: return
        try:
            r = requests.get(f"{API_URL}/products")
            if r.status_code == 200:
                self.products_cache = r.json()
                for p in self.products_cache:
                    self.tree.insert("", "end", values=(p['id'], p['nom'], p['stock'], p['prix']))
        except: pass

    def api_add(self):
        try:
            data = {"nom": self.e_nom.get(), "stock": self.e_stk.get(), "prix": self.e_prx.get()}
            requests.post(f"{API_URL}/products", json=data, headers={"Authorization": self.api_token})
            self.refresh_stock()
        except: pass

    def api_del(self):
        sel = self.tree.selection()
        if not sel: return
        pid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", "Supprimer ?"):
            requests.delete(f"{API_URL}/products/{pid}", headers={"Authorization": self.api_token})
            self.refresh_stock()

    def do_cmd(self):
        try:
            self.refresh_stock() # Important: Cache à jour
            pid, qty = int(self.ec_id.get()), int(self.ec_qt.get())
            prod = next((p for p in self.products_cache if p['id'] == pid), None)
            
            if not prod: return messagebox.showerror("Erreur", "ID inconnu")
            if prod['stock'] < qty: return messagebox.showerror("Stock", "Insuffisant")

            r = requests.put(f"{API_URL}/products/{pid}/stock", json={"qty": qty}, headers={"Authorization": self.api_token})
            
            if r.status_code == 200:
                tot = prod['prix'] * qty
                with open(FILE_CMD, 'a', encoding='utf-8', newline='') as f:
                    csv.writer(f).writerow([1, prod['nom'], qty, tot, datetime.now().strftime("%Y-%m-%d %H:%M")])
                
                messagebox.showinfo("Succès", "Commande validée")
                self.refresh_stock()
                self.load_histo()
                self.refresh_stats()
            else: messagebox.showerror("API", r.text)
        except ValueError: messagebox.showerror("Erreur", "Chiffres requis")

    def load_histo(self):
        for i in self.tree_cmd.get_children(): self.tree_cmd.delete(i)
        if os.path.exists(FILE_CMD):
            with open(FILE_CMD, 'r', encoding='utf-8') as f:
                next(f, None)
                for r in csv.reader(f): 
                    if r: self.tree_cmd.insert("", "end", values=r)

    def clean_histo(self):
        if os.path.exists(FILE_CMD):
            with open(FILE_CMD, 'w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(["id","prod","qte","tot","date"])
            self.load_histo()

    def refresh_stats(self):
        for w in self.fr_stat.winfo_children(): w.destroy()
        data = {}
        if os.path.exists(FILE_CMD):
            with open(FILE_CMD, 'r', encoding='utf-8') as f:
                next(f, None)
                for r in csv.reader(f):
                    if len(r)>2: data[r[1]] = data.get(r[1], 0) + int(r[2])
        
        if not data: return ctk.CTkLabel(self.fr_stat, text="Pas de données").pack()
        
        fig, ax = plt.subplots(figsize=(5,4))
        fig.patch.set_facecolor('#2b2b2b')
        ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', textprops={'color':"white"})
        FigureCanvasTkAgg(fig, master=self.fr_stat).get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()