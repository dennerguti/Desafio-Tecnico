from flask import Flask, render_template, request, session, send_file, redirect, url_for
import requests
import csv
import io

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

BASE_URL = "https://fakestoreapi.com"

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'cart' not in session:
        session['cart'] = {}

    search_query = request.form.get('search', '')

    if search_query:
        response = requests.get(f"{BASE_URL}/products")
        if response.status_code == 200:
            products = [p for p in response.json() if search_query.lower() in p['title'].lower()]
        else:
            products = []
    else:
        products = requests.get(f"{BASE_URL}/products").json()

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

    cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())

    return render_template('index.html', products=products, cart=session['cart'], cart_total=cart_total, search_query=search_query)

@app.route('/export')
def export_cart():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Título", "Preço", "Quantidade", "Imagem"])

    for item in session['cart'].values():
        writer.writerow([item['id'], item['title'], item['price'], item['quantity'], item['image']])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv", as_attachment=True, download_name="carrinho.csv")

@app.route('/import', methods=['POST'])
def import_cart():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400  

    file = request.files['file']
    if file.filename == '':
        return "Nenhum arquivo selecionado", 400  

    reader = csv.reader(io.StringIO(file.read().decode()), delimiter=",")
    next(reader)  

    for row in reader:
        if len(row) < 5:
            continue  

        product_id, title, price, quantity, image = row
        session['cart'][product_id] = {
            'id': product_id,
            'title': title,
            'price': float(price),
            'image': image,
            'quantity': int(quantity)
        }

    session.modified = True
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
