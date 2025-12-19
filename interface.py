import tkinter as tk
from tkinter import ttk, messagebox
import csv
import requests  # Pour parler à l'API
import fonction as f # Vos fonctions locales

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURATION API ---
API_URL = "http://127.0.0.1:5000/api/products"
# NOTE : J'ai supprimé la ligne API_TOKEN fixe ici, car elle va changer selon l'utilisateur.

f.init_files()

# --- GESTION INACTIVITÉ ---
TIMEOUT_LIMIT = 300000 
timer_id = None

# Variable pour savoir qui est connecté (par défaut commerçant)
CURRENT_USER_ROLE = "commercant" 

def reset_timer(event=None):
    global timer_id, fenetre
    if timer_id:
        try:
            fenetre.after_cancel(timer_id)
        except:
            pass
    timer_id = fenetre.after(TIMEOUT_LIMIT, deconnexion_automatique)

def deconnexion_automatique():
    messagebox.showwarning("Inactivité", "Vous avez été déconnecté pour inactivité.")
    deconnexion()

def deconnexion():
    global timer_id
    if timer_id:
        try:
            fenetre.after_cancel(timer_id)
        except:
            pass
    fenetre.destroy()
    import login
    login.LoginApp()

# =============================================================================
# LOGIQUE ONGLET STOCK (CONNECTÉ À L'API)
# =============================================================================

def charger_donnees_stock():
    """Récupère les produits depuis le SERVEUR API (Lecture publique)"""
    # 1. On vide le tableau
    for row in tableau_stock.get_children():
        tableau_stock.delete(row)
    
    try:
        # 2. GET est public, pas besoin de token
        response = requests.get(API_URL)
        
        if response.status_code == 200:
            produits = response.json()
            # 3. On remplit le tableau
            for p in produits:
                tableau_stock.insert("", tk.END, values=(p['id'], p['nom'], p['stock'], p['prix']))
        else:
            print("Erreur serveur:", response.status_code)
            
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erreur Connexion", "Impossible de joindre le serveur API.\nVérifiez que 'server.py' est lancé !")

def ajouter_produit_gui():
    """Envoie le nouveau produit au SERVEUR API (Écriture Sécurisée)"""
    nom_val = entry_nom.get()
    qte_val = entry_qte.get()
    prix_val = entry_prix.get()

    if not (nom_val and qte_val and prix_val):
        messagebox.showwarning("Attention", "Remplir tous les champs")
        return

    nouveau_produit = {
        "nom": nom_val,
        "stock": int(qte_val),
        "prix": float(prix_val)
    }

    # --- MODIFICATION DE SÉCURITÉ ICI ---
    # On choisit quel badge montrer au serveur selon le rôle
    if CURRENT_USER_ROLE == "admin":
        token_a_envoyer = "JE_SUIS_ADMIN_12345" # Le VRAI badge (doit être le même que server.py)
    else:
        token_a_envoyer = "TOKEN_INVALIDE"      # Un FAUX badge

    headers_securite = {
        "Authorization": token_a_envoyer,
        "Content-Type": "application/json"
    }
    # ------------------------------------

    try:
        # On ajoute 'headers=headers_securite'
        response = requests.post(API_URL, json=nouveau_produit, headers=headers_securite)
        
        if response.status_code == 201:
            messagebox.showinfo("Succès", f"Produit '{nom_val}' ajouté sur le serveur !")
            vider_champs_stock()
            rafraichir_tout()
        elif response.status_code == 403:
            # Message spécifique si le serveur refuse (Code 403)
            messagebox.showerror("Accès Refusé", "STOP ! Vous êtes connecté en tant que Commerçant.\nSeul l'ADMIN peut ajouter du stock.")
        else:
            messagebox.showerror("Erreur API", f"Le serveur a refusé : {response.text}")
            
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erreur", "Le serveur n'est pas connecté.")
    except ValueError:
        messagebox.showerror("Erreur", "Vérifiez que quantité et prix sont des nombres.")

def supprimer_produit_gui():
    messagebox.showinfo("Info", "La suppression via API n'est pas encore configurée sur le serveur.")

def clic_stock(event):
    selection = tableau_stock.selection()
    if selection:
        vals = tableau_stock.item(selection)['values']
        entry_id.delete(0, tk.END); entry_id.insert(0, vals[0])
        entry_nom.delete(0, tk.END); entry_nom.insert(0, vals[1])
        entry_qte.delete(0, tk.END); entry_qte.insert(0, vals[2])
        entry_prix.delete(0, tk.END); entry_prix.insert(0, vals[3])

def vider_champs_stock():
    entry_id.delete(0, tk.END); entry_nom.delete(0, tk.END)
    entry_qte.delete(0, tk.END); entry_prix.delete(0, tk.END)


# =============================================================================
# LOGIQUE ONGLET COMMANDES (Reste en local pour l'instant)
# =============================================================================

def charger_donnees_cmd():
    for row in tableau_cmd.get_children():
        tableau_cmd.delete(row)
    headers, data = f.lire_commandes()
    if data:
        for ligne in reversed(data):
            tableau_cmd.insert("", tk.END, values=ligne)

def action_creer_cmd():
    id_p = entry_cmd_idprod.get()
    qte = entry_cmd_qte.get()
    
    if not (id_p and qte):
        messagebox.showwarning("Erreur", "ID Produit et Quantité requis")
        return
        
    succes, msg = f.creer_commande(id_p, qte)
    if succes:
        messagebox.showinfo("Succès", msg)
        rafraichir_tout()
        entry_cmd_idprod.delete(0, tk.END)
        entry_cmd_qte.delete(0, tk.END)
    else:
        messagebox.showerror("Erreur", msg)

def action_supprimer_cmd():
    selection = tableau_cmd.selection()
    if not selection:
        messagebox.showwarning("Info", "Sélectionnez une commande à annuler")
        return
        
    vals = tableau_cmd.item(selection)['values']
    id_cmd = str(vals[0])
    
    if messagebox.askyesno("Confirmation", "Annuler cette commande ?\nLe stock sera remboursé."):
        succes, msg = f.supprimer_commande(id_cmd)
        if succes:
            messagebox.showinfo("Succès", msg)
            rafraichir_tout()
        else:
            messagebox.showerror("Erreur", msg)

def action_modifier_cmd():
    selection = tableau_cmd.selection()
    if not selection:
        messagebox.showwarning("Info", "Sélectionnez une commande à modifier")
        return
    
    vals = tableau_cmd.item(selection)['values']
    id_cmd = str(vals[0])
    nouvelle_qte = entry_cmd_qte.get()
    
    if not nouvelle_qte:
        messagebox.showwarning("Erreur", "Entrez la nouvelle quantité")
        return
        
    succes, msg = f.modifier_commande(id_cmd, nouvelle_qte)
    if succes:
        messagebox.showinfo("Succès", msg)
        rafraichir_tout()
    else:
        messagebox.showerror("Erreur", msg)

def clic_cmd(event):
    selection = tableau_cmd.selection()
    if selection:
        vals = tableau_cmd.item(selection)['values']
        entry_cmd_idprod.delete(0, tk.END); entry_cmd_idprod.insert(0, vals[1])
        entry_cmd_qte.delete(0, tk.END); entry_cmd_qte.insert(0, vals[3])

# =============================================================================
# LOGIQUE ONGLET STATISTIQUES (API + LOCAL)
# =============================================================================

def generer_graphiques():
    """Génère les graphiques Stock (API) et Ventes (Local)"""
    
    for widget in frame_canvas.winfo_children():
        widget.destroy()

    # 1. Récupération des données STOCK via API
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data_stock_api = response.json()
            noms_produits = [p['nom'] for p in data_stock_api]
            qtes_stock = [p['stock'] for p in data_stock_api]
        else:
            noms_produits, qtes_stock = [], []
    except:
        noms_produits, qtes_stock = [], []

    # 2. Récupération des données COMMANDES via fichier local
    h_cmd, data_cmd = f.lire_commandes()

    if not noms_produits and not qtes_stock:
        tk.Label(frame_canvas, text="Pas de données stock (Serveur éteint ?)").pack()
        return

    ventes_par_produit = {}
    if data_cmd:
        for cmd in data_cmd:
            nom = cmd[2]
            qte = int(cmd[3])
            ventes_par_produit[nom] = ventes_par_produit.get(nom, 0) + qte
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=100)
    fig.patch.set_facecolor('#f0f0f0')

    # Graphique 1 : Stock (Venant de l'API)
    couleurs = ['#4CAF50' if q > 5 else '#F44336' for q in qtes_stock]
    ax1.bar(noms_produits, qtes_stock, color=couleurs)
    ax1.set_title("Niveau de Stock (Serveur)", fontsize=10, fontweight='bold')
    ax1.set_ylabel("Quantité")
    ax1.tick_params(axis='x', rotation=45, labelsize=8)

    # Graphique 2 : Ventes (Venant du fichier local)
    if ventes_par_produit:
        labels = ventes_par_produit.keys()
        sizes = ventes_par_produit.values()
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax2.set_title("Répartition des Ventes", fontsize=10, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, "Aucune vente enregistrée", ha='center', va='center')
        ax2.axis('off')

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=frame_canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def rafraichir_tout():
    charger_donnees_stock()
    charger_donnees_cmd()
    generer_graphiques()

# =============================================================================
# LANCEMENT APP
# =============================================================================

# --- MODIFICATION DE LA SIGNATURE DE LA FONCTION ---
def lancer_app(role_connecte="commercant"):
    global fenetre, tableau_stock, entry_id, entry_nom, entry_qte, entry_prix
    global tableau_cmd, entry_cmd_idprod, entry_cmd_qte, frame_canvas
    
    # On stocke le rôle reçu depuis login.py
    global CURRENT_USER_ROLE
    CURRENT_USER_ROLE = role_connecte

    fenetre = tk.Tk()
    # On affiche le rôle dans le titre pour que ce soit clair
    fenetre.title(f"Système de Gestion - Connecté en tant que : {CURRENT_USER_ROLE.upper()}")
    fenetre.geometry("1000x700")
    
    fenetre.bind_all('<Any-KeyPress>', reset_timer)
    fenetre.bind_all('<Any-Motion>', reset_timer)
    
    reset_timer()
    
    header_frame = tk.Frame(fenetre, bg="#2C3E50", height=40)
    header_frame.pack(fill="x")
    
    btn_logout = tk.Button(header_frame, text="Se déconnecter", bg="#E74C3C", fg="white", 
                           font=("Arial", 10, "bold"), command=deconnexion)
    btn_logout.pack(side="right", padx=10, pady=5)
    
    lbl_titre = tk.Label(header_frame, text="TABLEAU DE BORD", bg="#2C3E50", fg="white", font=("Arial", 12, "bold"))
    lbl_titre.pack(side="left", padx=10)

    notebook = ttk.Notebook(fenetre)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    tab_stock = tk.Frame(notebook, bg="#f0f0f0")
    tab_cmd = tk.Frame(notebook, bg="#f0f0f0")
    tab_stats = tk.Frame(notebook, bg="#f0f0f0")

    notebook.add(tab_stock, text="📦 Gestion Stock (API)")
    notebook.add(tab_cmd, text="🛒 Gestion Commandes")
    notebook.add(tab_stats, text="📊 Statistiques")

    # --- STOCK TAB ---
    frame_form = tk.LabelFrame(tab_stock, text="Nouveau Produit (API)", padx=10, pady=10)
    frame_form.pack(fill="x", padx=10, pady=10)

    tk.Label(frame_form, text="ID (Auto)").grid(row=0, column=0); entry_id = tk.Entry(frame_form, state='disabled'); entry_id.grid(row=0, column=1)
    tk.Label(frame_form, text="Nom").grid(row=0, column=2); entry_nom = tk.Entry(frame_form); entry_nom.grid(row=0, column=3)
    tk.Label(frame_form, text="Qte").grid(row=0, column=4); entry_qte = tk.Entry(frame_form); entry_qte.grid(row=0, column=5)
    tk.Label(frame_form, text="Prix").grid(row=0, column=6); entry_prix = tk.Entry(frame_form); entry_prix.grid(row=0, column=7)

    f_btn_stock = tk.Frame(tab_stock); f_btn_stock.pack(pady=5)
    tk.Button(f_btn_stock, text="Ajouter (POST)", command=ajouter_produit_gui, bg="#4CAF50", fg="white").pack(side="left", padx=5)
    tk.Button(f_btn_stock, text="Vider Champs", command=vider_champs_stock, bg="#FF9800", fg="white").pack(side="left", padx=5)
    tk.Button(f_btn_stock, text="Supprimer", command=supprimer_produit_gui, bg="#9E9E9E", fg="white").pack(side="left", padx=5)

    tableau_stock = ttk.Treeview(tab_stock, columns=("id", "nom", "qte", "prix"), show="headings", height=8)
    tableau_stock.heading("id", text="ID"); tableau_stock.heading("nom", text="Nom"); tableau_stock.heading("qte", text="Stock"); tableau_stock.heading("prix", text="Prix")
    tableau_stock.pack(fill="both", expand=True, padx=10, pady=10)
    tableau_stock.bind("<ButtonRelease-1>", clic_stock)

    # --- CMD TAB ---
    frame_cmd_form = tk.LabelFrame(tab_cmd, text="Action Commande (Local)", padx=10, pady=10)
    frame_cmd_form.pack(fill="x", padx=10, pady=10)

    tk.Label(frame_cmd_form, text="ID Produit :").grid(row=0, column=0, padx=5)
    entry_cmd_idprod = tk.Entry(frame_cmd_form)
    entry_cmd_idprod.grid(row=0, column=1, padx=5)

    tk.Label(frame_cmd_form, text="Quantité :").grid(row=0, column=2, padx=5)
    entry_cmd_qte = tk.Entry(frame_cmd_form)
    entry_cmd_qte.grid(row=0, column=3, padx=5)

    f_btn_cmd = tk.Frame(tab_cmd); f_btn_cmd.pack(pady=5)
    tk.Button(f_btn_cmd, text="✚ Nouvelle Commande", command=action_creer_cmd, bg="#4CAF50", fg="white").pack(side="left", padx=5)
    tk.Button(f_btn_cmd, text="✎ Modifier (Qte)", command=action_modifier_cmd, bg="#2196F3", fg="white").pack(side="left", padx=5)
    tk.Button(f_btn_cmd, text="✖ Annuler Commande", command=action_supprimer_cmd, bg="#F44336", fg="white").pack(side="left", padx=5)

    tableau_cmd = ttk.Treeview(tab_cmd, columns=("id", "pid", "nom", "qte", "total", "date"), show="headings")
    tableau_cmd.heading("id", text="ID Cmd"); tableau_cmd.heading("pid", text="ID Prod"); tableau_cmd.heading("nom", text="Produit")
    tableau_cmd.heading("qte", text="Qte Vendue"); tableau_cmd.heading("total", text="Total €"); tableau_cmd.heading("date", text="Date")
    tableau_cmd.pack(fill="both", expand=True, padx=10, pady=10)
    tableau_cmd.bind("<ButtonRelease-1>", clic_cmd)

    # --- STATS TAB ---
    btn_refresh = tk.Button(tab_stats, text="🔄 Actualiser les Graphiques", command=rafraichir_tout, bg="#607D8B", fg="white")
    btn_refresh.pack(pady=10)

    frame_canvas = tk.Frame(tab_stats, bg="#f0f0f0")
    frame_canvas.pack(fill="both", expand=True, padx=10, pady=10)

    rafraichir_tout()
    fenetre.mainloop()

if __name__ == "__main__":
    lancer_app()