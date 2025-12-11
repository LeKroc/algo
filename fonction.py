import csv
import os
from datetime import datetime 

File_stock = 'data.csv'
File_commande = 'commande.csv'

def init_files():
    """Initialise les fichiers s'ils n'existent pas"""
    if not os.path.exists(File_stock):
        create_csv() # Utilise votre fonction existante
    
    if not os.path.exists(File_commande):
        headers = ["id_cmd", "id_prod", "nom_prod", "qte", "total", "date"]
        with open(File_commande, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

# --- DEFINITION DES FONCTIONS ---

def create_csv():
    donnees = [
        ["id", "nom_produit", "quantité", "prix"],
        [1, "Stylo", 10, 1.5],
        [2, "Cahier", 5, 3.0],
        [3, "Gomme", 20, 0.5],
        [4, "Crayon", 15, 0.75],
        [5, "Feutre", 8, 2.0]
    ]
    with open('data.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(donnees)
    print("Fichier 'data.csv' (ré)initialisé.")

def parcourir():
    try:
        with open('data.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader, None) 
            if headers:
                data = list(reader)    
                return headers, data
            return [], []
    except FileNotFoundError:
        return None, None
    
def lire_commandes():
    """Lit le fichier commandes"""
    try:
        with open(File_commande, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader, None)
            if headers:
                return headers, list(reader)
            return [], []
    except FileNotFoundError:
        return [], []
def sauvegarder_csv(headers, data):
    """Sauvegarde générique pour le stock"""
    with open(File_stock, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

def sauvegarder_cmd_csv(headers, data):
    """Sauvegarde générique pour les commandes"""
    with open(File_commande, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)
def update_stock_quantite(id_prod, delta):
    """
    Modifie le stock d'un produit.
    delta < 0 : on retire du stock (vente).
    delta > 0 : on remet du stock (annulation).
    Retourne (True, msg) ou (False, msg).
    """
    headers, data = parcourir()
    if not data: return False, "Fichier stock vide."
    
    found = False
    for ligne in data:
        if ligne[0] == str(id_prod):
            found = True
            stock_actuel = int(ligne[2])
            nouveau_stock = stock_actuel + delta
            
            if nouveau_stock < 0:
                return False, f"Stock insuffisant (Dispo: {stock_actuel})"
            
            ligne[2] = str(nouveau_stock)
            break
            
    if not found:
        return False, "ID Produit introuvable."
    
    sauvegarder_csv(headers, data)
    return True, "Stock mis à jour."

def creer_commande(id_prod, qte_voulue):
    """CREATE: Vérifie le stock, le décrémente et crée la commande"""
 
    try:
        qte_voulue = int(qte_voulue)
        if qte_voulue <= 0: return False, "La quantité doit être positive."
    except ValueError: return False, "Quantité invalide."

    
    headers, data = parcourir()
    produit = next((p for p in data if p[0] == str(id_prod)), None)
    if not produit: return False, "Produit inexistant."

    nom_prod = produit[1]
    prix_unit = float(produit[3])

    
    succes_stock, msg_stock = update_stock_quantite(id_prod, -qte_voulue)
    if not succes_stock:
        return False, msg_stock

    
    h_cmd, data_cmd = lire_commandes()
    
    ids = [int(row[0]) for row in data_cmd if row[0].isdigit()]
    new_id_cmd = max(ids) + 1 if ids else 1
    
    total = prix_unit * qte_voulue
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    nouvelle_cmd = [new_id_cmd, id_prod, nom_prod, qte_voulue, total, date_str]
    
    with open(File_commande, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        if os.path.getsize(File_commande) == 0: 
             writer.writerow(["id_cmd", "id_prod", "nom_prod", "qte", "total", "date"])
        writer.writerow(nouvelle_cmd)

    return True, f"Commande #{new_id_cmd} validée."

def supprimer_commande(id_cmd):
    """DELETE: Supprime la commande et REMBOURSE le stock"""
    h_cmd, data_cmd = lire_commandes()
    cmd_a_supprimer = None
    index = -1

    # Trouver la commande
    for i, row in enumerate(data_cmd):
        if row[0] == str(id_cmd):
            cmd_a_supprimer = row
            index = i
            break
    
    if not cmd_a_supprimer: return False, "Commande introuvable."

    id_prod = cmd_a_supprimer[1]
    qte_a_rembourser = int(cmd_a_supprimer[3])

    # 1. Rembourser le stock
    update_stock_quantite(id_prod, qte_a_rembourser)

    # 2. Supprimer la ligne
    del data_cmd[index]
    sauvegarder_cmd_csv(h_cmd, data_cmd)

    return True, "Commande annulée et stock remboursé."

def modifier_commande(id_cmd, nouvelle_qte):
    """UPDATE: Modifie la quantité et ajuste le stock (Différence)"""
    try:
        nouvelle_qte = int(nouvelle_qte)
        if nouvelle_qte <= 0: return False, "Qte doit être > 0."
    except: return False, "Erreur format quantité."

    h_cmd, data_cmd = lire_commandes()
    cmd = None
    idx = -1
    for i, row in enumerate(data_cmd):
        if row[0] == str(id_cmd):
            cmd = row
            idx = i
            break
    
    if not cmd: return False, "Commande introuvable."

    id_prod = cmd[1]
    ancienne_qte = int(cmd[3])
    
   
    diff_stock = ancienne_qte - nouvelle_qte

    succes, msg = update_stock_quantite(id_prod, diff_stock)
    if not succes: return False, msg

    # Mise à jour commande
    # On doit relire le produit pour le prix unitaire
    headers_stk, data_stk = parcourir()
    prod = next((p for p in data_stk if p[0] == str(id_prod)), None)
    prix = float(prod[3])

    cmd[3] = str(nouvelle_qte)
    cmd[4] = str(nouvelle_qte * prix) # Nouveau total
    cmd[5] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (Modif)"
    
    data_cmd[idx] = cmd
    sauvegarder_cmd_csv(h_cmd, data_cmd)
    
    return True, "Commande mise à jour."

if __name__ == "__main__":
    init_files()
    print("Fichiers initialisés.")




def sauvegarder_csv(headers, data_triee):
    with open('data.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data_triee)
    print("-> Fichier 'data.csv' mis à jour !")

def recherche_produit(nom_produit):
    headers, data = parcourir()
    if data:
        resultats = [ligne for ligne in data if nom_produit.lower() in ligne[1].lower()]
        if resultats:
            print(f"Produits trouvés pour '{nom_produit}':")
            print(headers)
            for ligne in resultats:
                print(ligne)
        else:
            print(f"Aucun produit trouvé pour '{nom_produit}'.")
    else:
        print("Le fichier 'data.csv' est vide ou n'existe pas.")

def recherche_id(nbr_id):
    headers, data = parcourir()
    if data: 
        resultats = [ligne for ligne in data if ligne[0] == nbr_id]
        if resultats:
            print(f"Produit trouvé pour l'ID '{nbr_id}':")
            print(headers)
            for ligne in resultats:
                print(ligne)

def recherche_quantite(nbr_quantite):
    headers, data = parcourir()
    if data:
        resultats = [ligne for ligne in data if ligne[2] == nbr_quantite]
        if resultats:
            print(f"Produits trouvés pour la quantité '{nbr_quantite}':")
            print(headers)
            for ligne in resultats:
                print(ligne)

def recherche_prix(prix):
    headers, data = parcourir()
    if data:
        resultats = [ligne for ligne in data if ligne[3] == prix]
        if resultats:
            print(f"Produits trouvés pour le prix '{prix}':")
            print(headers)
            for ligne in resultats:
                print(ligne)

# --- PROGRAMME PRINCIPAL (PROTÉGÉ) ---
# Ce bloc ne s'exécute QUE si vous lancez "python fonction.py"
# Il ne s'exécute PAS si vous faites "import fonction"

if __name__ == "__main__":
    create_csv()
    en_tetes, contenu = parcourir()
    
    sort = input("\n[Choisissez le critère de tri : 1 - ID | 2 - Nom | 3 - Quantité | 4 - Prix :] \n[-> ")

    if contenu:
        if sort == '1':
            contenu.sort(key=lambda x: int(x[0]))
        elif sort == '2':
            contenu.sort(key=lambda x: x[1].lower())
        elif sort == '3':
            contenu.sort(key=lambda x: int(x[2]))
        elif sort == '4':
            contenu.sort(key=lambda x: float(x[3]))
        else:
            print("Choix invalide. Tri par défaut par ID.")
            contenu.sort(key=lambda x: int(x[0]))

        sauvegarder_csv(en_tetes, contenu)

    nbr_id = input("\n[Entrez l'ID du produit à rechercher :] \n[-> ")
    recherche_id(nbr_id)
    nom_recherche = input("\n[Entrez le nom du produit à rechercher :] \n[-> ")
    recherche_produit(nom_recherche)
    nbr_quantite = input("\n[Entrez la quantité du produit à rechercher :] \n[-> ")
    recherche_quantite(nbr_quantite)
    prix = input("\n[Entrez le prix du produit à rechercher :] \n[-> ")
    recherche_prix(prix)
    