from flask import Blueprint, render_template, request, send_file, redirect, url_for, jsonify, make_response
import requests
import csv
import io
import datetime
from .models import CartItem, User
from .auth import token_required
from . import db

main_bp = Blueprint('main', __name__)
BASE_URL = "https://fakestoreapi.com"

@main_bp.route('/api', methods=['GET', 'POST'])
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

    return render_template(
        'index.html',
        products=products,
        cart=cart_items,
        cart_total=cart_total,
        search_query=search_query,
        username=current_user.username
    )

@main_bp.route('/export')
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

@main_bp.route('/import', methods=['POST'])
@token_required
def import_cart(current_user):
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files['file']
    if file.filename == '':
        return "Nenhum arquivo selecionado", 400

    CartItem.query.filter_by(user_id=current_user.id).delete()
    
    reader = csv.reader(io.StringIO(file.read().decode()), delimiter=",")
    next(reader)

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
    return redirect(url_for('main.index'))