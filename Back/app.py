from flask import Flask, render_template, request, session, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import csv
import io
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

BASE_URL = "https://fakestoreapi.com"

# Modelos do banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)

# Criar banco de dados e tabelas
with app.app_context():
    db.create_all()
    # Arrumar essa senha
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Credenciais inválidas")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
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

            # Verificar se o produto já está no carrinho
            cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
            
            if cart_item:
                cart_item.quantity += quantity
            else:
                new_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    title=product['title'],
                    price=product['price'],
                    image=product['image'],
                    quantity=quantity
                )
                db.session.add(new_item)
            db.session.commit()

        elif 'remove_from_cart' in request.form:
            product_id = request.form['product_id']
            cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
            
            if cart_item:
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                else:
                    db.session.delete(cart_item)
                db.session.commit()

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    cart_total = sum(item.price * item.quantity for item in cart_items)

    return render_template(
        'index.html',
        products=products,
        cart=cart_items,
        cart_total=cart_total,
        search_query=search_query
    )

@app.route('/export')
def export_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Título", "Preço", "Quantidade", "Imagem"])

    for item in cart_items:
        writer.writerow([item.product_id, item.title, item.price, item.quantity, item.image])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="carrinho.csv"
    )

@app.route('/import', methods=['POST'])
def import_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400  

    file = request.files['file']
    if file.filename == '':
        return "Nenhum arquivo selecionado", 400  

    CartItem.query.filter_by(user_id=user_id).delete()
    
    reader = csv.reader(io.StringIO(file.read().decode()), delimiter=",")
    next(reader) 

    for row in reader:
        if len(row) < 5:
            continue  

        product_id, title, price, quantity, image = row
        new_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            title=title,
            price=float(price),
            image=image,
            quantity=int(quantity)
        )
        db.session.add(new_item)

    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)