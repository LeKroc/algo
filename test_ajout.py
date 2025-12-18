import requests

url = "http://127.0.0.1:5000/api/products"
nouveau_produit = {
    "nom": "Règle Graduée",
    "stock": 50,
    "prix": 1.25
}

print("Envoi de la demande d'ajout...")
reponse = requests.post(url, json=nouveau_produit)

if reponse.status_code == 201:
    print("✅ SUCCÈS ! Produit ajouté :", reponse.json())
else:
    print("❌ ERREUR :", reponse.text)