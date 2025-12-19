from flask import Flask, jsonify, request
import uuid 
app = Flask(__name__)

# ==========================================
# 1. DONNÉES (Simulation Base de Données)
# ==========================================

produits_db = [
    {"id": 1, "nom": "Stylo", "stock": 10, "prix": 1.5},
    {"id": 2, "nom": "Cahier", "stock": 5, "prix": 3.0},
]


users_db = {
    "admin": "admin123",     
    "commercant": "vente123"  
}

active_tokens = {}

# ==========================================
# 2. ROUTE D'AUTHENTIFICATION (La nouveauté)
# ==========================================

@app.route('/')
def home():
    return "✅ Serveur AUTHENTIFIÉ en ligne !"

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')

    if username in users_db and users_db[username] == password:
       
        token = str(uuid.uuid4()) 
        
        
        role = "admin" if username == "admin" else "commercant"
        active_tokens[token] = role
        
        print(f"🔑 Nouvelle connexion : {username} (Role: {role}) - Token: {token}")
        
        return jsonify({
            "token": token, 
            "role": role, 
            "message": "Connexion réussie"
        }), 200
    else:
        return jsonify({"erreur": "Identifiants incorrects"}), 401


# ==========================================
# 3. ROUTES PRODUITS (Sécurisées par Token)
# ==========================================

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(produits_db)

@app.route('/api/products', methods=['POST'])
def add_product():
    token_recu = request.headers.get('Authorization')
    
    
    if token_recu not in active_tokens:
        return jsonify({"erreur": "Token invalide ou expiré. Veuillez vous reconnecter."}), 401
    
    role_utilisateur = active_tokens[token_recu]
    
    if role_utilisateur != "admin":
        return jsonify({"erreur": "Accès refusé ! Seul l'admin peut ajouter."}), 403

    
    nouvel_element = request.get_json()
    if not nouvel_element or 'nom' not in nouvel_element:
        return jsonify({"erreur": "Nom obligatoire"}), 400

    nouveau_id = produits_db[-1]['id'] + 1 if produits_db else 1
    produit_a_ajouter = {
        "id": nouveau_id,
        "nom": nouvel_element['nom'],
        "stock": nouvel_element.get('stock', 0), 
        "prix": nouvel_element.get('prix', 0.0)  
    }
    produits_db.append(produit_a_ajouter)
    return jsonify(produit_a_ajouter), 201

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    token_recu = request.headers.get('Authorization')
    
    if token_recu not in active_tokens:
        return jsonify({"erreur": "Non connecté."}), 401
        
    if active_tokens[token_recu] != "admin":
        return jsonify({"erreur": "Accès refusé ! Vous n'êtes pas admin."}), 403

 
    produit_trouve = None
    for p in produits_db:
        if p['id'] == product_id:
            produit_trouve = p
            break
    
    if produit_trouve:
        produits_db.remove(produit_trouve)
        return jsonify({"message": f"Produit ID {product_id} supprimé."}), 200
    else:
        return jsonify({"erreur": "Produit introuvable."}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)