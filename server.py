import hashlib
import hmac
from flask import Flask, jsonify, request
import uuid 
import csv
import os

app = Flask(__name__)

# --- CONFIGURATION ---
CSV_DATA_FILE = 'data.csv'   # Stock des produits
CSV_USER_FILE = 'users.csv'  # Base utilisateurs

# ==========================================
# 1. GESTION PRODUITS (DATA.CSV)
# ==========================================
def init_csv():
    if not os.path.exists(CSV_DATA_FILE):
        with open(CSV_DATA_FILE, 'w', encoding='utf-8', newline='') as f:
            csv.writer(f).writerow(["id", "nom", "stock", "prix"])

def read_products():
    products = []
    if os.path.exists(CSV_DATA_FILE):
        with open(CSV_DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    products.append({
                        "id": int(row["id"]),
                        "nom": row["nom"],
                        "stock": int(row["stock"]),
                        "prix": float(row["prix"])
                    })
                except ValueError: continue 
    return products

def write_products(products):
    with open(CSV_DATA_FILE, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ["id", "nom", "stock", "prix"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

init_csv()

# ==========================================
# 2. AUTHENTIFICATION (USERS.CSV)
# ==========================================
active_tokens = {} # {token: role}

def verifier_identifiants_csv(username_input, password_input):
    if not os.path.exists(CSV_USER_FILE):
        return None, "Fichier utilisateurs introuvable (Inscrivez-vous via l'app)"

    with open(CSV_USER_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row: continue
            # Format attendu: [username, salt, hash, role]
            if row[0] == username_input:
                try:
                    salt = row[1]
                    stored_hash = row[2]
                    role = row[3]
                    
                    # Vérification crypto
                    key = hashlib.pbkdf2_hmac('sha256', password_input.encode('utf-8'), salt.encode('utf-8'), 100000)
                    if hmac.compare_digest(stored_hash, key.hex()):
                        return role, "Succès"
                except IndexError: continue
                    
    return None, "Identifiants incorrects"

@app.route('/')
def home(): return "✅ SERVEUR EN LIGNE"

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    role, msg = verifier_identifiants_csv(data.get('username'), data.get('password'))

    if role:
        token = str(uuid.uuid4())
        active_tokens[token] = role
        print(f"[LOGIN] {data.get('username')} ({role}) connecté.")
        return jsonify({"token": token, "role": role}), 200
    return jsonify({"erreur": msg}), 401

# ==========================================
# 3. ENDPOINTS PRODUITS
# ==========================================

# GET (Voir)
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(read_products()), 200

# POST (Ajouter - Admin & Commerçant)
@app.route('/api/products', methods=['POST'])
def add_product():
    token = request.headers.get('Authorization')
    if token not in active_tokens: return jsonify({"erreur": "Non connecté"}), 403
    
    data = request.get_json()
    products = read_products()
    new_id = max([p['id'] for p in products]) + 1 if products else 1
    
    new_prod = {
        "id": new_id,
        "nom": data['nom'],
        "stock": int(data.get('stock', 0)),
        "prix": float(data.get('prix', 0.0))
    }
    products.append(new_prod)
    write_products(products)
    print(f"[AJOUT] {new_prod['nom']} (ID: {new_id})")
    return jsonify(new_prod), 201

# PUT (Modifier Stock/Commander - Admin & Commerçant)
@app.route('/api/products/<int:id>/stock', methods=['PUT'])
def update_stock(id):
    token = request.headers.get('Authorization')
    if token not in active_tokens: return jsonify({"erreur": "Non connecté"}), 401

    data = request.get_json()
    qty = int(data.get('qty', 0))
    products = read_products()
    
    for p in products:
        if p['id'] == id:
            if p['stock'] >= qty:
                p['stock'] -= qty
                write_products(products)
                print(f"[VENTE] ID {id} (-{qty})")
                return jsonify({"message": "Stock mis à jour"}), 200
            return jsonify({"erreur": f"Stock insuffisant (Reste: {p['stock']})"}), 400
            
    return jsonify({"erreur": "Produit introuvable"}), 404

# DELETE (Supprimer - Admin SEULEMENT)
@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    token = request.headers.get('Authorization')
    if token not in active_tokens or active_tokens[token] != "admin":
        return jsonify({"erreur": "Action réservée aux Admins"}), 403

    products = read_products()
    new_list = [p for p in products if p['id'] != id]
    
    if len(new_list) < len(products):
        write_products(new_list)
        print(f"[DELETE] ID {id} supprimé")
        return jsonify({"message": "Produit supprimé"}), 200
    return jsonify({"erreur": "ID introuvable"}), 404

if __name__ == '__main__':
    print("--- SERVEUR LANCÉ SUR PORT 5000 ---")
    app.run(debug=True, port=5000)