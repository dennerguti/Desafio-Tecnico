from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# URL
BASE_URL = "https://fakestoreapi.com"

@app.route('/', methods=['GET', 'POST'])
def index():
    products = []
    search_query = ""
    
    if request.method == 'POST':
        search_query = request.form.get('search', '')
        if search_query:
            # Busca 
            all_products = requests.get(f"{BASE_URL}/products").json()
            products = [
                p for p in all_products 
                if search_query.lower() in p['title'].lower() or 
                   search_query.lower() in p['description'].lower()
            ]
        else:
            # Mostra todos
            products = requests.get(f"{BASE_URL}/products").json()
    
    return render_template('index.html', products=products, search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)