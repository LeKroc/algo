from flask import Flask, jsonify, request

app = Flask(__name__)

# --- LA CLÉ DE SÉCURITÉ (LE BADGE) ---
# Dans la vraie vie, ce token est généré dynamiquement lors du login.
# Pour l'instant, on utilise un mot de passe fixe pour l'API.
API_SECRET_TOKEN = "JE_SUIS_ADMIN_12345"

produits_db = [
    {"id": 1, "nom": "Stylo", "stock": 10, "prix": 1.5},
    {"id": 2, "nom": "Cahier", "stock": 5, "prix": 3.0},
]

@app.route('/')
def home():
    return "✅ Serveur SÉCURISÉ en ligne !"

# Route Publique (Tout le monde peut voir les produits)
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(produits_db)

# Route PRIVÉE (Seul l'admin peut ajouter)
@app.route('/api/products', methods=['POST'])
def add_product():
    # 1. ON VÉRIFIE LE BADGE (HEADER)
    # On regarde si la requête contient l'en-tête "Authorization"
    token_recu = request.headers.get('Authorization')
    
    if token_recu != API_SECRET_TOKEN:
        # Si le token est mauvais ou absent -> ERREUR 403 (INTERDIT)
        return jsonify({"erreur": "Accès refusé ! Vous n'êtes pas admin."}), 403

    # 2. Si le badge est bon, on continue...
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
    app.run(debug=True, port=5000)