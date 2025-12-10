import csv

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