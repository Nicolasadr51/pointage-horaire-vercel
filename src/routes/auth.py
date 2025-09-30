from flask import Blueprint, request, jsonify, session
from functools import wraps
import hashlib
from src.models.employee import db, Employee

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(password, hashed):
    """Vérifier un mot de passe"""
    return hash_password(password) == hashed

def login_required(f):
    """Décorateur pour vérifier l'authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return jsonify({'error': 'Authentification requise'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour vérifier les droits administrateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return jsonify({'error': 'Authentification requise'}), 401
        
        employee = Employee.query.get(session['employee_id'])
        if not employee or not employee.is_admin:
            return jsonify({'error': 'Droits administrateur requis'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    """Connexion d'un employé"""
    try:
        data = request.get_json()
        employee_number = data.get('employee_number')
        password = data.get('password')
        
        if not employee_number or not password:
            return jsonify({'error': 'Numéro d\'employé et mot de passe requis'}), 400
        
        # Rechercher l'employé
        employee = Employee.query.filter_by(employee_number=employee_number).first()
        
        if not employee:
            return jsonify({'error': 'Employé non trouvé'}), 401
        
        if not employee.is_active:
            return jsonify({'error': 'Compte désactivé'}), 401
        
        # Vérifier le mot de passe
        if not check_password(password, employee.password_hash):
            return jsonify({'error': 'Mot de passe incorrect'}), 401
        
        # Créer la session
        session['employee_id'] = employee.id
        session['is_admin'] = employee.is_admin
        
        return jsonify({
            'message': 'Connexion réussie',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la connexion: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Déconnexion"""
    session.clear()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Récupérer les informations de l'utilisateur connecté"""
    try:
        employee = Employee.query.get(session['employee_id'])
        if not employee:
            session.clear()
            return jsonify({'error': 'Utilisateur non trouvé'}), 401
        
        return jsonify({'employee': employee.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération du profil: {str(e)}'}), 500
