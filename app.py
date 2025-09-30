#!/usr/bin/env python3
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, send_from_directory, send_file
from flask_cors import CORS
from src.models.employee import db
from src.routes.auth import auth_bp
from src.routes.employee import employee_bp
from src.routes.timeentry import timeentry_bp
from src.routes.export import export_bp

app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration pour la production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pointeuse_production_key_2024_secure_v2')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'pointeuse:'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS en production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuration de la base de données
database_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation des extensions
db.init_app(app)
CORS(app, supports_credentials=True, origins=['*'])

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(employee_bp, url_prefix='/api')
app.register_blueprint(timeentry_bp, url_prefix='/api')
app.register_blueprint(export_bp, url_prefix='/api')

# Création des tables et initialisation
with app.app_context():
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    db.create_all()
    
    # Vérifier si l'admin existe, sinon le créer
    from src.models.employee import Employee
    from src.routes.auth import hash_password
    
    admin = Employee.query.filter_by(employee_number='ADMIN001').first()
    if not admin:
        admin = Employee(
            employee_number='ADMIN001',
            first_name='Administrateur',
            last_name='Système',
            email='admin@pointeuse.local',
            password_hash=hash_password('admin123'),
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

@app.route('/health')
def health():
    """Point de contrôle de santé pour le déploiement"""
    return {'status': 'healthy', 'app': 'pointeuse-horaire'}, 200

@app.route('/')
def serve_frontend():
    """Servir la page d'accueil du frontend"""
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/<path:path>')
def serve_static_files(path):
    """Servir les fichiers statiques du frontend"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # Si le fichier n'existe pas, servir index.html pour le routing côté client
        return send_file(os.path.join(app.static_folder, 'index.html'))

# Pour Vercel
if __name__ == "__main__":
    app.run(debug=False)
