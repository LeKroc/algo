import tkinter as tk
from tkinter import ttk, messagebox
import csv
import fonction as f 

def charger_donnees():
    """Lit le CSV via fonction.py et remplit le tableau"""
    
    for row in tableau.get_children():
        tableau.delete(row)
    
   
    headers, data = f.parcourir()
    
    if data:
        for ligne in data:
             tableau.insert("", tk.END, values=ligne)

def ajouter_produit_gui():
    """Récupère les infos des champs et ajoute au CSV"""
    id_val = entry_id.get()
    nom_val = entry_nom.get()
    qte_val = entry_qte.get()
    prix_val = entry_prix.get()

    if not id_val or not nom_val or not qte_val or not prix_val:
        messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
        return

    
    headers, data = f.parcourir()
    if data:
        ids = [ligne[0] for ligne in data]
        if id_val in ids:
            messagebox.showerror("Erreur", f"L'ID {id_val} existe déjà !")
            return

    
    with open('data.csv', 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([id_val, nom_val, qte_val, prix_val])
    
 
    vider_champs()
    charger_donnees()
    messagebox.showinfo("Succès", f"Produit '{nom_val}' ajouté !")

def supprimer_produit_gui():
    """Supprime la ligne sélectionnée"""
    selection = tableau.selection()
    if not selection:
        messagebox.showwarning("Attention", "Veuillez sélectionner un produit à supprimer")
        return

    
    item = tableau.item(selection)
    valeurs = item['values']
    id_a_supprimer = str(valeurs[0])

   
    headers, data = f.parcourir()
    nouvelles_donnees = [ligne for ligne in data if ligne[0] != id_a_supprimer]

   
    f.sauvegarder_csv(headers, nouvelles_donnees)
    
    vider_champs()
    charger_donnees()
    messagebox.showinfo("Supprimé", "Le produit a été supprimé.")

def remplir_champs_via_clic(event):
    """Quand on clique sur une ligne, ça remplit les champs (pratique !)"""
    selection = tableau.selection()
    if selection:
        item = tableau.item(selection)
        valeurs = item['values']
        
       
        entry_id.delete(0, tk.END)
        entry_id.insert(0, valeurs[0])
        
        entry_nom.delete(0, tk.END)
        entry_nom.insert(0, valeurs[1])
        
        entry_qte.delete(0, tk.END)
        entry_qte.insert(0, valeurs[2])
        
        entry_prix.delete(0, tk.END)
        entry_prix.insert(0, valeurs[3])

def vider_champs():
    entry_id.delete(0, tk.END)
    entry_nom.delete(0, tk.END)
    entry_qte.delete(0, tk.END)
    entry_prix.delete(0, tk.END)



fenetre = tk.Tk()
fenetre.title("Gestion de Stock - Commerçant")
fenetre.geometry("800x600")
fenetre.configure(bg="#f0f0f0") 


f.create_csv()


frame_form = tk.LabelFrame(fenetre, text="Détails du produit", padx=10, pady=10, bg="#f0f0f0")
frame_form.pack(fill="x", padx=20, pady=10)


tk.Label(frame_form, text="ID :", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5)
entry_id = tk.Entry(frame_form)
entry_id.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_form, text="Nom :", bg="#f0f0f0").grid(row=0, column=2, padx=5, pady=5)
entry_nom = tk.Entry(frame_form)
entry_nom.grid(row=0, column=3, padx=5, pady=5)

tk.Label(frame_form, text="Quantité :", bg="#f0f0f0").grid(row=0, column=4, padx=5, pady=5)
entry_qte = tk.Entry(frame_form)
entry_qte.grid(row=0, column=5, padx=5, pady=5)

tk.Label(frame_form, text="Prix (€) :", bg="#f0f0f0").grid(row=0, column=6, padx=5, pady=5)
entry_prix = tk.Entry(frame_form)
entry_prix.grid(row=0, column=7, padx=5, pady=5)


frame_boutons = tk.Frame(fenetre, bg="#f0f0f0")
frame_boutons.pack(pady=10)

btn_ajouter = tk.Button(frame_boutons, text="Ajouter", command=ajouter_produit_gui, bg="#4CAF50", fg="white", width=15)
btn_ajouter.pack(side="left", padx=10)

btn_vider = tk.Button(frame_boutons, text="Vider champs", command=vider_champs, bg="#FF9800", fg="white", width=15)
btn_vider.pack(side="left", padx=10)

btn_supprimer = tk.Button(frame_boutons, text="Supprimer sélection", command=supprimer_produit_gui, bg="#F44336", fg="white", width=15)
btn_supprimer.pack(side="left", padx=10)


frame_tableau = tk.Frame(fenetre)
frame_tableau.pack(fill="both", expand=True, padx=20, pady=20)


columns = ("id", "nom", "qte", "prix")
tableau = ttk.Treeview(frame_tableau, columns=columns, show="headings")


tableau.heading("id", text="ID")
tableau.heading("nom", text="Nom du Produit")
tableau.heading("qte", text="Quantité")
tableau.heading("prix", text="Prix Unitaire (€)")


tableau.column("id", width=50, anchor="center")
tableau.column("nom", width=300)
tableau.column("qte", width=100, anchor="center")
tableau.column("prix", width=100, anchor="center")


scrollbar = ttk.Scrollbar(frame_tableau, orient="vertical", command=tableau.yview)
tableau.configure(yscroll=scrollbar.set)
scrollbar.pack(side="right", fill="y")
tableau.pack(fill="both", expand=True)

tableau.bind("<ButtonRelease-1>", remplir_champs_via_clic)


charger_donnees()
fenetre.mainloop()