from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import datetime

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.secret_key = os.urandom(24)

    
    # Configurações
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'desafio'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
    
    db.init_app(app)
    
    from .auth import auth_bp
    from .routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    with app.app_context():
        db.create_all()
        from .models import User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
    
    return app