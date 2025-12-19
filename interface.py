import tkinter as tk
from tkinter import ttk, messagebox
import requests  
import fonction as f 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# 1. VARIABLES GLOBALES & INIT
# ==========================================

# URL de l'API
API_BASE_URL = "http://127.0.0.1:5000/api"

# Variables pour stocker les composants graphiques
fenetre = None
entry_id = None
entry_nom = None
entry_qte = None
entry_prix = None
tableau_stock = None
entry_cmd_idprod = None
entry_cmd_qte = None
tableau_cmd = None
frame_canvas = None

# Variables de Session
CURRENT_USER_ROLE = "commercant" 
JWT_TOKEN = None  
TIMEOUT_LIMIT = 300000 
timer_id = None

# Init fichiers locaux
f.init_files()

# ==========================================
# 2. GESTION AUTHENTIFICATION & TIMEOUT
# ==========================================

def authentification_automatique(role_voulu):
    global JWT_TOKEN
    
    if role_voulu == "admin":
        creds = {"username": "admin", "password": "admin123"}
    else:
        creds = {"username": "commercant", "password": "vente123"}

    try:
        url_login = f"{API_BASE_URL}/auth/login"
        print(f"🔵 Connexion en cours vers {url_login}...")
        response = requests.post(url_login, json=creds)

        if response.status_code == 200:
            data = response.json()
            JWT_TOKEN = data['token']
            print(f"✅ TOKEN REÇU : {JWT_TOKEN[:15]}...")
            return True
        else:
            print(f"❌ Échec Auth : {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        messagebox.showerror("Fatal", "Le serveur API n'est pas lancé !")
        return False

def reset_timer(event=None):
    global timer_id, fenetre
    if timer_id:
        try: fenetre.after_cancel(timer_id)
        except: pass
    timer_id = fenetre.after(TIMEOUT_LIMIT, deconnexion_automatique)

def deconnexion_automatique():
    messagebox.showwarning("Inactivité", "Vous avez été déconnecté.")
    deconnexion()

def deconnexion():
    global timer_id
    if timer_id:
        try: fenetre.after_cancel(timer_id)
        except: pass
    fenetre.destroy()

# ==========================================
# 3. FONCTIONS DE CHARGEMENT & STATS
# ==========================================

def charger_donnees_stock():
    """Récupère les produits depuis l'API"""
    if tableau_stock is None: return 
    
    for row in tableau_stock.get_children():
        tableau_stock.delete(row)
    
    try:
        response = requests.get(f"{API_BASE_URL}/products")
        if response.status_code == 200:
            produits = response.json()
            for p in produits:
                tableau_stock.insert("", tk.END, values=(p['id'], p['nom'], p['stock'], p['prix']))
            
    except requests.exceptions.ConnectionError:
        pass

def charger_donnees_cmd():
    """Récupère les commandes locales"""
    if tableau_cmd is None: return

    for row in tableau_cmd.get_children():
        tableau_cmd.delete(row)
    
    headers, data = f.lire_commandes()
    if data:
        for ligne in reversed(data):
            tableau_cmd.insert("", tk.END, values=ligne)

def generer_graphiques():
    """Génère les graphiques Matplotlib"""
    if frame_canvas is None: return

    # Nettoyer l'ancien graphique
    for widget in frame_canvas.winfo_children(): widget.destroy()
    
    # --- 1. Récupération Données Stock (API) ---
    try:
        resp = requests.get(f"{API_BASE_URL}/products")
        data_stock = resp.json() if resp.status_code == 200 else []
    except: data_stock = []

    noms = [p['nom'] for p in data_stock]
    qtes = [p['stock'] for p in data_stock]

    # --- 2. Récupération Données Ventes (Local) ---
    _, data_cmd = f.lire_commandes()
    ventes = {}
    
    # Calcul des ventes par produit (Nom du produit est à l'index 2, Qté à l'index 3)
    if data_cmd:
        for c in data_cmd: 
            try:
                nom_produit = c[2]
                quantite = int(c[3])
                ventes[nom_produit] = ventes.get(nom_produit, 0) + quantite
            except (IndexError, ValueError):
                continue

    # --- 3. Création de la Figure ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=100)
    fig.patch.set_facecolor('#f0f0f0') # Couleur de fond gris clair
    
    # Graphique 1 : Barres (Stock)
    if noms:
        ax1.bar(noms, qtes, color=['#4CAF50' if x>5 else 'red' for x in qtes])
        ax1.set_title("Stock Actuel (API)")
        ax1.tick_params(axis='x', rotation=45) # Rotation des noms si trop longs
    else:
        ax1.text(0.5, 0.5, "Pas de données API", ha='center', va='center')
        ax1.set_title("Stock (Vide)")
    
    # Graphique 2 : Camembert (Ventes)
    if ventes:
        ax2.pie(ventes.values(), labels=ventes.keys(), autopct='%1.1f%%', startangle=90)
        ax2.set_title("Répartition des Ventes")
    else:
        # Affiche un texte si aucune vente n'est faite
        ax2.text(0.5, 0.5, "Aucune vente enregistrée", ha='center', va='center')
        ax2.set_title("Ventes (Vide)")
    
    # Affichage sur Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame_canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def rafraichir_tout():
    """Fonction centrale de mise à jour"""
    charger_donnees_stock()
    charger_donnees_cmd()
    generer_graphiques()

# ==========================================
# 4. ACTIONS UTILISATEUR (Boutons)
# ==========================================

# --- STOCK (API) ---

def ajouter_produit_gui():
    nom_val = entry_nom.get()
    qte_val = entry_qte.get()
    prix_val = entry_prix.get()

    if not (nom_val and qte_val and prix_val):
        messagebox.showwarning("Attention", "Remplir tous les champs")
        return

    nouveau_produit = {"nom": nom_val, "stock": int(qte_val), "prix": float(prix_val)}
    headers_securite = {"Authorization": JWT_TOKEN} if JWT_TOKEN else {}

    try:
        response = requests.post(f"{API_BASE_URL}/products", json=nouveau_produit, headers=headers_securite)
        
        if response.status_code == 201:
            messagebox.showinfo("Succès", "Produit ajouté !")
            vider_champs_stock()
            rafraichir_tout()
        elif response.status_code == 403:
            messagebox.showerror("INTERDIT", "Réservé aux Admins")
        elif response.status_code == 401:
            messagebox.showerror("Erreur", "Token invalide")
        else:
            messagebox.showerror("Erreur API", response.text)
            
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erreur", "Serveur déconnecté")
    except ValueError:
        messagebox.showerror("Erreur", "Vérifiez les nombres")

def supprimer_produit_gui():
    selection = tableau_stock.selection()
    if not selection:
        messagebox.showwarning("Attention", "Sélectionnez une ligne")
        return

    vals = tableau_stock.item(selection)['values']
    id_produit = vals[0]

    if not messagebox.askyesno("Confirmation", f"Supprimer ID {id_produit} ?"): return

    headers_securite = {"Authorization": JWT_TOKEN} if JWT_TOKEN else {}

    try:
        response = requests.delete(f"{API_BASE_URL}/products/{id_produit}", headers=headers_securite)
        if response.status_code == 200:
            messagebox.showinfo("Succès", "Supprimé !")
            vider_champs_stock()
            rafraichir_tout()
        elif response.status_code == 403:
            messagebox.showerror("INTERDIT", "Réservé aux Admins")
        else:
            messagebox.showerror("Erreur", f"Code : {response.status_code}")
    except:
        messagebox.showerror("Erreur", "Problème connexion")

def clic_stock(event):
    selection = tableau_stock.selection()
    if selection:
        vals = tableau_stock.item(selection)['values']
        entry_id.configure(state='normal')
        entry_id.delete(0, tk.END); entry_id.insert(0, vals[0])
        entry_id.configure(state='disabled')
        entry_nom.delete(0, tk.END); entry_nom.insert(0, vals[1])
        entry_qte.delete(0, tk.END); entry_qte.insert(0, vals[2])
        entry_prix.delete(0, tk.END); entry_prix.insert(0, vals[3])

def vider_champs_stock():
    entry_id.configure(state='normal'); entry_id.delete(0, tk.END); entry_id.configure(state='disabled')
    entry_nom.delete(0, tk.END)
    entry_qte.delete(0, tk.END); entry_prix.delete(0, tk.END)

# --- COMMANDES (LOCAL) ---

def action_creer_cmd():
    id_p = entry_cmd_idprod.get()
    qte = entry_cmd_qte.get()
    if not (id_p and qte): return
    succes, msg = f.creer_commande(id_p, qte)
    if succes:
        messagebox.showinfo("Succès", msg)
        rafraichir_tout()
        entry_cmd_idprod.delete(0, tk.END); entry_cmd_qte.delete(0, tk.END)
    else:
        messagebox.showerror("Erreur", msg)

def action_modifier_cmd():
    selection = tableau_cmd.selection()
    if not selection: return
    nouvelle_qte = entry_cmd_qte.get()
    if not nouvelle_qte: return
    f.modifier_commande(str(tableau_cmd.item(selection)['values'][0]), nouvelle_qte)
    rafraichir_tout()

def action_supprimer_cmd():
    selection = tableau_cmd.selection()
    if not selection: return
    vals = tableau_cmd.item(selection)['values']
    if messagebox.askyesno("Confirm", "Annuler commande ?"):
        f.supprimer_commande(str(vals[0]))
        rafraichir_tout()

def clic_cmd(event):
    selection = tableau_cmd.selection()
    if selection:
        vals = tableau_cmd.item(selection)['values']
        entry_cmd_idprod.delete(0, tk.END); entry_cmd_idprod.insert(0, vals[1])
        entry_cmd_qte.delete(0, tk.END); entry_cmd_qte.insert(0, vals[3])

# ==========================================
# 5. CONSTRUCTION INTERFACE (Main)
# ==========================================

def lancer_app(role_connecte="commercant"):
    global fenetre, tableau_stock, entry_id, entry_nom, entry_qte, entry_prix
    global tableau_cmd, entry_cmd_idprod, entry_cmd_qte, frame_canvas
    global CURRENT_USER_ROLE
    
    CURRENT_USER_ROLE = role_connecte

    # Connexion API Initiale
    authentification_automatique(role_connecte)

    # Fenêtre Principale
    fenetre = tk.Tk()
    fenetre.title(f"Système JWT - Rôle : {CURRENT_USER_ROLE.upper()}")
    fenetre.geometry("1000x700")
    
    fenetre.bind_all('<Any-KeyPress>', reset_timer)
    fenetre.bind_all('<Any-Motion>', reset_timer)
    reset_timer()
    
    # En-tête
    header = tk.Frame(fenetre, bg="#2C3E50", height=40); header.pack(fill="x")
    tk.Label(header, text=f"SESSION : {CURRENT_USER_ROLE.upper()}", bg="#2C3E50", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)
    tk.Button(header, text="Se déconnecter", bg="#E74C3C", fg="white", command=deconnexion).pack(side="right", padx=10, pady=5)

    notebook = ttk.Notebook(fenetre); notebook.pack(fill='both', expand=True, padx=10, pady=10)
    tab_stock = tk.Frame(notebook); tab_cmd = tk.Frame(notebook); tab_stats = tk.Frame(notebook)
    notebook.add(tab_stock, text="Gestion Stock (API)"); notebook.add(tab_cmd, text="Commandes"); notebook.add(tab_stats, text="Stats")

    # --- TAB STOCK ---
    form = tk.LabelFrame(tab_stock, text="Produit"); form.pack(fill="x", padx=10, pady=5)
    tk.Label(form, text="ID").pack(side="left"); entry_id = tk.Entry(form, width=5, state='disabled'); entry_id.pack(side="left")
    tk.Label(form, text="Nom").pack(side="left"); entry_nom = tk.Entry(form); entry_nom.pack(side="left")
    tk.Label(form, text="Qte").pack(side="left"); entry_qte = tk.Entry(form, width=5); entry_qte.pack(side="left")
    tk.Label(form, text="Prix").pack(side="left"); entry_prix = tk.Entry(form, width=10); entry_prix.pack(side="left")
    
    btns = tk.Frame(tab_stock); btns.pack(pady=5)
    tk.Button(btns, text="Ajouter (Admin)", command=ajouter_produit_gui, bg="#4CAF50", fg="white").pack(side="left", padx=5)
    tk.Button(btns, text="Supprimer (Admin)", command=supprimer_produit_gui, bg="#F44336", fg="white").pack(side="left", padx=5)
    tk.Button(btns, text="Vider", command=vider_champs_stock).pack(side="left", padx=5)

    tableau_stock = ttk.Treeview(tab_stock, columns=("id", "nom", "qte", "prix"), show="headings", height=8)
    for col in ["id", "nom", "qte", "prix"]: tableau_stock.heading(col, text=col.capitalize())
    tableau_stock.pack(fill="both", expand=True, padx=10)
    tableau_stock.bind("<ButtonRelease-1>", clic_stock)

    # --- TAB CMD ---
    f_cmd = tk.LabelFrame(tab_cmd, text="Commande"); f_cmd.pack(fill="x", padx=10, pady=5)
    tk.Label(f_cmd, text="ID Prod").pack(side="left"); entry_cmd_idprod = tk.Entry(f_cmd); entry_cmd_idprod.pack(side="left")
    tk.Label(f_cmd, text="Qte").pack(side="left"); entry_cmd_qte = tk.Entry(f_cmd); entry_cmd_qte.pack(side="left")
    
    b_cmd = tk.Frame(tab_cmd); b_cmd.pack(pady=5)
    tk.Button(b_cmd, text="Nouvelle", command=action_creer_cmd, bg="#4CAF50").pack(side="left", padx=5)
    tk.Button(b_cmd, text="Modifier", command=action_modifier_cmd, bg="#2196F3").pack(side="left", padx=5)
    tk.Button(b_cmd, text="Annuler", command=action_supprimer_cmd, bg="#F44336").pack(side="left", padx=5)

    tableau_cmd = ttk.Treeview(tab_cmd, columns=("id", "pid", "nom", "qte", "total", "date"), show="headings")
    for col in ["id", "pid", "nom", "qte", "total", "date"]: tableau_cmd.heading(col, text=col)
    tableau_cmd.pack(fill="both", expand=True, padx=10)
    tableau_cmd.bind("<ButtonRelease-1>", clic_cmd)

    # --- TAB STATS ---
    tk.Button(tab_stats, text="Actualiser", command=rafraichir_tout).pack(pady=5)
    frame_canvas = tk.Frame(tab_stats); frame_canvas.pack(fill="both", expand=True)

    # Premier chargement
    rafraichir_tout()
    fenetre.mainloop()

if __name__ == "__main__":
    lancer_app("admin")