from fonction import *
import csv

def ajout_produit():
    # On récupère les données pour vérifier les ID
    header, data = parcourir()
    
    # Création de la liste des IDs existants pour éviter les doublons
    if data: 
        ids_existants = [ligne[0] for ligne in data]
    else:
        ids_existants = []
        
    print("\n--- NOUVEAU PRODUIT ---")

    # 1. Validation de l'ID (boucle tant que ce n'est pas bon)
    while True:
        new_id = input("Entrez l'ID (entier unique) : ")
        if new_id in ids_existants:
            print(f"Erreur : L'ID {new_id} existe déjà.")
        elif not new_id.isdigit(): # Vérifie si c'est bien un nombre entier
            print("Erreur : Veuillez entrer un nombre entier.")
        else:
            break # On sort de la boucle si tout est bon
    
    # 2. Nom du produit
    nom = input("Nom du produit : ")

    # 3. Validation Quantité
    while True:
        try:
            qte_input = input("Quantité : ")
            qte = int(qte_input) # On convertit pour vérifier
            break
        except ValueError:
            print("Erreur : Veuillez entrer un nombre entier pour la quantité.")

    # 4. Validation Prix
    while True:
        try:
            prix_input = input("Prix : ")
            prix = float(prix_input) # On convertit pour vérifier
            break
        except ValueError:
            print("Erreur : Veuillez entrer un nombre valide pour le prix (ex: 10.5).")

    # Enregistrement
    with open('data.csv', 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([new_id, nom, qte, prix])
    
    print(f"-> Succès : Le produit '{nom}' (ID: {new_id}) a été ajouté !")

# IMPORTANT : Il faut appeler la fonction pour qu'elle s'exécute !
if __name__ == "__main__":
    ajout_produit()