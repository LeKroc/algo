from flask import Flask, jsonify, request

app = Flask(__name__)

produits_db = [
    {"id": 1, "nom": "Stylo", "stock": 10, "prix": 1.5},
    {"id": 2, "nom": "Cahier", "stock": 5, "prix": 3.0},
    {"id": 3, "nom": "Gomme", "stock": 20, "prix": 0.5},
    {"id": 4, "nom": "Crayon", "stock": 15, "prix": 0.75},
    {"id": 5, "nom": "Feutre", "stock": 8, "prix": 2.0}
]

@app.route('/')
def home():
    return "✅ Le serveur API est EN LIGNE !"

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(produits_db)

@app.route('/api/products/<int:id_produit>', methods=['GET'])
def get_product_detail(id_produit):
    for produit in produits_db:
        if produit["id"] == id_produit:
            return jsonify(produit)
    return jsonify({"erreur": "Produit non trouvé"}), 404

@app.route('/api/products', methods=['POST'])
def add_product():
    nouvel_element = request.get_json()
    
    if not nouvel_element or 'nom' not in nouvel_element:
        return jsonify({"erreur": "Le champ 'nom' est obligatoire"}), 400

    nouveau_id = produits_db[-1]['id'] + 1 if produits_db else 1
    
    
    produit_a_ajouter = {
        "id": nouveau_id,
        "nom": nouvel_element['nom'],
        "stock": nouvel_element.get('stock', 0), 
        "prix": nouvel_element.get('prix', 0.0)  
    }
    
    produits_db.append(produit_a_ajouter)
    
    return jsonify(produit_a_ajouter), 201

if __name__ == '__main__':
    print("Démarrage du serveur sur le port 5000...")
    app.run(debug=True, port=5000)