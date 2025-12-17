from flask import Flask, jsonify, request

app = Flask(__name__)

produits_db = [
    [1, "Stylo", 10, 1.5],
        [2, "Cahier", 5, 3.0],
        [3, "Gomme", 20, 0.5],
        [4, "Crayon", 15, 0.75],
        [5, "Feutre", 8, 2.0]
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

if __name__ == '__main__':
    print("Démarrage du serveur sur le port 5000...")
    app.run(debug=True, port=5000)