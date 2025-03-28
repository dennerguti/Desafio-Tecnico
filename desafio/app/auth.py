from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
import jwt
import datetime
from functools import wraps
from .models import User
from . import db, create_app

auth_bp = Blueprint('auth', __name__)

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
            data = jwt.decode(token, create_app().config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado!'}), 401
        except:
            return jsonify({'message': 'Token é inválido!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + create_app().config['JWT_ACCESS_TOKEN_EXPIRES']
            }, create_app().config['JWT_SECRET_KEY'])
            
            response = make_response(redirect(url_for('main.index', token=token)))
            response.set_cookie('token', token)
            return response
        else:
            return render_template('login.html', error="Credenciais inválidas")
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie('token')
    return response