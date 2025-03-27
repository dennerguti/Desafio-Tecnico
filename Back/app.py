from flask import Flask, render_template, request, session, Response
import requests

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

BASE_URL = "https://fakestoreapi.com"

@app.route('/', methods=['GET', 'POST'])
def index():
    products = []
    search_query = ""

    if 'cart' not in session:
        session['cart'] = {}

    if request.method == 'POST':
        if 'add_to_cart' in request.form:
            product_id = request.form['product_id']
            quantity = int(request.form.get('quantity', 1))
            product = requests.get(f"{BASE_URL}/products/{product_id}").json()
            
            if product_id in session['cart']:
                session['cart'][product_id]['quantity'] += quantity
            else:
                session['cart'][product_id] = {
                    'id': product_id,
                    'title': product['title'],
                    'price': product['price'],
                    'image': product['image'],
                    'quantity': quantity
                }
            session.modified = True  
            
        elif 'remove_from_cart' in request.form:
            product_id = request.form['product_id']
            if product_id in session['cart']:
                if session['cart'][product_id]['quantity'] > 1:
                    session['cart'][product_id]['quantity'] -= 1
                else:
                    del session['cart'][product_id]
                session.modified = True  

    products = requests.get(f"{BASE_URL}/products").json()
    cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())

    return render_template('index.html', products=products, cart=session['cart'], cart_total=cart_total)

@app.route('/export')
def export_cart():
    cart = session.get('cart', {})
    
    if not cart:
        return "O carrinho está vazio.", 400

    def generate():
        yield "ID,Produto,Quantidade,Preço Unitário,Subtotal\n"
        for item in cart.values():
            yield f"{item['id']},{item['title']},{item['quantity']},{item['price']},{item['price'] * item['quantity']}\n"

    return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=carrinho.csv"})

if __name__ == '__main__':
    app.run(debug=True)
