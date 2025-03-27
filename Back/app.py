from flask import Flask, render_template, request, jsonify, session
import requests

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para usar sessions

# URL
BASE_URL = "https://fakestoreapi.com"

@app.route('/', methods=['GET', 'POST'])
def index():
    products = []
    search_query = ""
    
    # Inicializa o carrinho na session se não existir
    if 'cart' not in session:
        session['cart'] = {}
    
    if request.method == 'POST':
        # Verifica se é uma ação de adicionar ao carrinho
        if 'add_to_cart' in request.form:
            product_id = request.form['product_id']
            quantity = int(request.form.get('quantity', 1))  # Pega a quantidade do formulário
            
            # Busca o produto na API
            product = requests.get(f"{BASE_URL}/products/{product_id}").json()
            
            # Adiciona ou atualiza o produto no carrinho
            if product_id in session['cart']:
                session['cart'][product_id]['quantity'] += quantity
            else:
                session['cart'][product_id] = {
                    'id': product_id,
                    'title': product['title'],
                    'price': product['price'],
                    'description': product['description'],
                    'image': product['image'],
                    'quantity': quantity
                }
            session.modified = True
            
        # Verifica se é uma ação de remover do carrinho
        elif 'remove_from_cart' in request.form:
            product_id = request.form['product_id']
            if product_id in session['cart']:
                if session['cart'][product_id]['quantity'] > 1:
                    session['cart'][product_id]['quantity'] -= 1
                else:
                    del session['cart'][product_id]
                session.modified = True
        
        # Verifica se é uma busca
        elif 'search' in request.form:
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
    
    # Se não foi uma busca, mostra todos os produtos
    if not products and request.method != 'POST':
        products = requests.get(f"{BASE_URL}/products").json()
    
    # Calcula total do carrinho
    cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
    
    return render_template(
        'index.html', 
        products=products, 
        search_query=search_query,
        cart=session['cart'],
        cart_total=cart_total
    )

if __name__ == '__main__':
    app.run(debug=True)
