from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import csv
import io
import os
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuração do banco de dados e JWT
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.urandom(24)  # Chave secreta para JWT
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)  # Tempo de expiração do token
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
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('123456')  # Mudar isso depois
        db.session.add(admin)
        db.session.commit()

# Decorator para verificar o token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'token' in request.args:
            token = request.args.get('token')
        elif request.method == 'POST' and 'token' in request.form:
            token = request.form['token']
        elif 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        elif 'token' in request.cookies:
            token = request.cookies.get('token')
        
        if not token:
            return jsonify({'message': 'Token está faltando!'}), 401
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado!'}), 401
        except:
            return jsonify({'message': 'Token é inválido!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):

            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
            }, app.config['JWT_SECRET_KEY'])
            
            response = make_response(redirect(url_for('index', token=token)))
            response.set_cookie('token', token)
            return response
        else:
            return render_template('login.html', error="Credenciais inválidas")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('token')
    return response

@app.route('/api', methods=['GET', 'POST'])
@token_required
def index(current_user):
    search_query = request.form.get('search', '')
    user_id = current_user.id

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

    response = make_response(render_template(
        'index.html',
        products=products,
        cart=cart_items,
        cart_total=cart_total,
        search_query=search_query,
        username=current_user.username
    ))
    
    token = request.args.get('token')
    if token:
        response.set_cookie('token', token)
    
    return response

@app.route('/export')
@token_required
def export_cart(current_user):
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

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
@token_required
def import_cart(current_user):
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files['file']
    if file.filename == '':
        return "Nenhum arquivo selecionado", 400

    # Limpar carrinho atual
    CartItem.query.filter_by(user_id=current_user.id).delete()
    
    reader = csv.reader(io.StringIO(file.read().decode()), delimiter=",")
    next(reader)  # Pular cabeçalho

    for row in reader:
        if len(row) < 5:
            continue

        product_id, title, price, quantity, image = row
        new_item = CartItem(
            user_id=current_user.id,
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