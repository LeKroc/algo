import tkinter as tk
from tkinter import ttk, messagebox
import csv
import fonction as f

# --- IMPORTS POUR LES GRAPHIQUES ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- INITIALISATION ---
f.init_files()

# =============================================================================
# LOGIQUE ONGLET STOCK
# =============================================================================

def charger_donnees_stock():
    for row in tableau_stock.get_children():
        tableau_stock.delete(row)
    headers, data = f.parcourir()
    if data:
        for ligne in data:
            tableau_stock.insert("", tk.END, values=ligne)

def ajouter_produit_gui():
    id_val, nom_val = entry_id.get(), entry_nom.get()
    qte_val, prix_val = entry_qte.get(), entry_prix.get()

    if not (id_val and nom_val and qte_val and prix_val):
        messagebox.showwarning("Attention", "Remplir tous les champs")
        return

    headers, data = f.parcourir()
    if data and any(l[0] == id_val for l in data):
        messagebox.showerror("Erreur", f"L'ID {id_val} existe déjà !")
        return

    with open(f.FILE_STOCK, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([id_val, nom_val, qte_val, prix_val])
    
    vider_champs_stock()
    rafraichir_tout()
    messagebox.showinfo("Succès", f"Produit '{nom_val}' ajouté !")

def supprimer_produit_gui():
    selection = tableau_stock.selection()
    if not selection:
        messagebox.showwarning("Attention", "Sélectionnez un produit")
        return
    
    valeurs = tableau_stock.item(selection)['values']
    id_suppr = str(valeurs[0])
    
    h, data = f.parcourir()
    new_data = [l for l in data if l[0] != id_suppr]
    f.sauvegarder_csv(h, new_data)
    
    vider_champs_stock()
    rafraichir_tout()

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
# LOGIQUE ONGLET COMMANDES
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
# LOGIQUE ONGLET STATISTIQUES (MATPLOTLIB)
# =============================================================================

def generer_graphiques():
    """Génère les graphiques Stock et Ventes"""
    # 1. Nettoyage de l'ancienne figure si elle existe
    for widget in frame_canvas.winfo_children():
        widget.destroy()

    # 2. Récupération des données
    h_stock, data_stock = f.parcourir()
    h_cmd, data_cmd = f.lire_commandes()

    if not data_stock:
        tk.Label(frame_canvas, text="Pas de données stock à afficher").pack()
        return

    # --- Préparation Données STOCK ---
    noms_produits = [ligne[1] for ligne in data_stock]
    qtes_stock = [int(ligne[2]) for ligne in data_stock]

    # --- Préparation Données VENTES ---
    ventes_par_produit = {}
    if data_cmd:
        for cmd in data_cmd:
            nom = cmd[2]
            qte = int(cmd[3])
            ventes_par_produit[nom] = ventes_par_produit.get(nom, 0) + qte

    # 3. Création de la figure Matplotlib
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), dpi=100)
    fig.patch.set_facecolor('#f0f0f0')

    # --- GRAPHIQUE 1 : Bar Chart (Stock) ---
    couleurs = ['#4CAF50' if q > 5 else '#F44336' for q in qtes_stock]
    ax1.bar(noms_produits, qtes_stock, color=couleurs)
    ax1.set_title("Niveau de Stock Actuel", fontsize=10, fontweight='bold')
    ax1.set_ylabel("Quantité")
    ax1.tick_params(axis='x', rotation=45, labelsize=8)

    # --- GRAPHIQUE 2 : Pie Chart (Ventes) ---
    if ventes_par_produit:
        labels = ventes_par_produit.keys()
        sizes = ventes_par_produit.values()
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax2.set_title("Répartition des Ventes", fontsize=10, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, "Aucune vente enregistrée", ha='center', va='center')
        ax2.axis('off')

    plt.tight_layout()

    # 4. Intégration dans Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame_canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def rafraichir_tout():
    charger_donnees_stock()
    charger_donnees_cmd()
    generer_graphiques()

# =============================================================================
# FONCTION DE LANCEMENT DE L'APPLICATION (ETAPE 3)
# =============================================================================

def lancer_app():
    # On rend les variables globales pour que les fonctions (ajouter_produit_gui, etc.) puissent les voir
    global fenetre, tableau_stock, entry_id, entry_nom, entry_qte, entry_prix
    global tableau_cmd, entry_cmd_idprod, entry_cmd_qte, frame_canvas

    fenetre = tk.Tk()
    fenetre.title("Système de Gestion Complet")
    fenetre.geometry("1000x700")

    # Création des onglets
    notebook = ttk.Notebook(fenetre)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    tab_stock = tk.Frame(notebook, bg="#f0f0f0")
    tab_cmd = tk.Frame(notebook, bg="#f0f0f0")
    tab_stats = tk.Frame(notebook, bg="#f0f0f0")

    notebook.add(tab_stock, text="📦 Gestion Stock")
    notebook.add(tab_cmd, text="🛒 Gestion Commandes")
    notebook.add(tab_stats, text="📊 Statistiques")

    # --- CONTENU ONGLET 1 : STOCK ---
    frame_form = tk.LabelFrame(tab_stock, text="Produit", padx=10, pady=10)
    frame_form.pack(fill="x", padx=10, pady=10)

    tk.Label(frame_form, text="ID").grid(row=0, column=0); entry_id = tk.Entry(frame_form); entry_id.grid(row=0, column=1)
    tk.Label(frame_form, text="Nom").grid(row=0, column=2); entry_nom = tk.Entry(frame_form); entry_nom.grid(row=0, column=3)
    tk.Label(frame_form, text="Qte").grid(row=0, column=4); entry_qte = tk.Entry(frame_form); entry_qte.grid(row=0, column=5)
    tk.Label(frame_form, text="Prix").grid(row=0, column=6); entry_prix = tk.Entry(frame_form); entry_prix.grid(row=0, column=7)

    f_btn_stock = tk.Frame(tab_stock); f_btn_stock.pack(pady=5)
    tk.Button(f_btn_stock, text="Ajouter", command=ajouter_produit_gui, bg="#4CAF50", fg="white").pack(side="left", padx=5)
    tk.Button(f_btn_stock, text="Vider", command=vider_champs_stock, bg="#FF9800", fg="white").pack(side="left", padx=5)
    tk.Button(f_btn_stock, text="Supprimer", command=supprimer_produit_gui, bg="#F44336", fg="white").pack(side="left", padx=5)

    tableau_stock = ttk.Treeview(tab_stock, columns=("id", "nom", "qte", "prix"), show="headings", height=8)
    tableau_stock.heading("id", text="ID"); tableau_stock.heading("nom", text="Nom"); tableau_stock.heading("qte", text="Stock"); tableau_stock.heading("prix", text="Prix")
    tableau_stock.pack(fill="both", expand=True, padx=10, pady=10)
    tableau_stock.bind("<ButtonRelease-1>", clic_stock)

    # --- CONTENU ONGLET 2 : COMMANDES ---
    frame_cmd_form = tk.LabelFrame(tab_cmd, text="Action Commande", padx=10, pady=10)
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

    # --- CONTENU ONGLET 3 : STATISTIQUES ---
    btn_refresh = tk.Button(tab_stats, text="🔄 Actualiser les Graphiques", command=rafraichir_tout, bg="#607D8B", fg="white")
    btn_refresh.pack(pady=10)

    frame_canvas = tk.Frame(tab_stats, bg="#f0f0f0")
    frame_canvas.pack(fill="both", expand=True, padx=10, pady=10)

    # --- DEMARRAGE ---
    rafraichir_tout()
    fenetre.mainloop()

# Bloc de sécurité : permet d'importer ce fichier sans qu'il se lance tout seul
if __name__ == "__main__":
    lancer_app()