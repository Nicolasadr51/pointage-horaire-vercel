from flask import Blueprint, request, jsonify, session
import hashlib

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
from src.models.employee import db, Employee
from src.routes.auth import login_required, admin_required

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Récupérer le profil de l'employé connecté"""
    try:
        employee = Employee.query.get(session['employee_id'])
        if not employee:
            return jsonify({'error': 'Employé non trouvé'}), 404
        
        return jsonify({'employee': employee.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération du profil: {str(e)}'}), 500

@employee_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Mettre à jour le profil de l'employé connecté"""
    try:
        data = request.get_json()
        employee = Employee.query.get(session['employee_id'])
        
        if not employee:
            return jsonify({'error': 'Employé non trouvé'}), 404
        
        # Champs modifiables par l'employé
        if 'first_name' in data:
            employee.first_name = data['first_name']
        if 'last_name' in data:
            employee.last_name = data['last_name']
        if 'email' in data:
            # Vérifier l'unicité de l'email
            existing = Employee.query.filter(
                Employee.email == data['email'],
                Employee.id != employee.id
            ).first()
            if existing:
                return jsonify({'error': 'Cet email est déjà utilisé'}), 400
            employee.email = data['email']
        
        # Changement de mot de passe
        if 'current_password' in data and 'new_password' in data:
            if not hash_password(data["current_password"]) == employee.password_hash:
                return jsonify({'error': 'Mot de passe actuel incorrect'}), 400
            
            if len(data['new_password']) < 6:
                return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 6 caractères'}), 400
            
            employee.password_hash = hash_password(data["password"])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500

# Routes administrateur

@employee_bp.route('/admin/employees', methods=['GET'])
@admin_required
def get_employees():
    """Récupérer la liste des employés (admin seulement)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        # Limiter le nombre d'éléments par page
        per_page = min(per_page, 100)
        
        query = Employee.query
        
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                db.or_(
                    Employee.first_name.ilike(search_filter),
                    Employee.last_name.ilike(search_filter),
                    Employee.employee_number.ilike(search_filter),
                    Employee.email.ilike(search_filter)
                )
            )
        
        query = query.order_by(Employee.last_name, Employee.first_name)
        employees = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'employees': [emp.to_dict() for emp in employees.items],
            'total': employees.total,
            'pages': employees.pages,
            'current_page': employees.page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération des employés: {str(e)}'}), 500

@employee_bp.route('/admin/employees', methods=['POST'])
@admin_required
def create_employee():
    """Créer un nouvel employé (admin seulement)"""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['employee_number', 'first_name', 'last_name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier l'unicité du numéro d'employé
        if Employee.query.filter_by(employee_number=data['employee_number']).first():
            return jsonify({'error': 'Ce numéro d\'employé existe déjà'}), 400
        
        # Vérifier l'unicité de l'email
        if Employee.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Cet email est déjà utilisé'}), 400
        
        # Validation du mot de passe
        if len(data['password']) < 6:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        
        # Créer l'employé
        employee = Employee(
            employee_number=data['employee_number'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password_hash=hash_password(data['password']),
            is_admin=data.get('is_admin', False),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({
            'message': 'Employé créé avec succès',
            'employee': employee.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la création: {str(e)}'}), 500

@employee_bp.route('/admin/employees/<int:employee_id>', methods=['GET'])
@admin_required
def get_employee(employee_id):
    """Récupérer un employé spécifique (admin seulement)"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        return jsonify({'employee': employee.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération: {str(e)}'}), 500

@employee_bp.route('/admin/employees/<int:employee_id>', methods=['PUT'])
@admin_required
def update_employee(employee_id):
    """Mettre à jour un employé (admin seulement)"""
    try:
        data = request.get_json()
        employee = Employee.query.get_or_404(employee_id)
        
        # Mettre à jour les champs
        if 'employee_number' in data:
            # Vérifier l'unicité
            existing = Employee.query.filter(
                Employee.employee_number == data['employee_number'],
                Employee.id != employee_id
            ).first()
            if existing:
                return jsonify({'error': 'Ce numéro d\'employé existe déjà'}), 400
            employee.employee_number = data['employee_number']
        
        if 'first_name' in data:
            employee.first_name = data['first_name']
        if 'last_name' in data:
            employee.last_name = data['last_name']
        
        if 'email' in data:
            # Vérifier l'unicité
            existing = Employee.query.filter(
                Employee.email == data['email'],
                Employee.id != employee_id
            ).first()
            if existing:
                return jsonify({'error': 'Cet email est déjà utilisé'}), 400
            employee.email = data['email']
        
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
            employee.password_hash = hash_password(data["password"])
        
        if 'is_admin' in data:
            employee.is_admin = data['is_admin']
        if 'is_active' in data:
            employee.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Employé mis à jour avec succès',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500

@employee_bp.route('/admin/employees/<int:employee_id>', methods=['DELETE'])
@admin_required
def delete_employee(employee_id):
    """Supprimer un employé (admin seulement)"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # Empêcher la suppression de son propre compte
        if employee.id == session['employee_id']:
            return jsonify({'error': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
        
        # Soft delete : désactiver plutôt que supprimer
        employee.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Employé désactivé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la suppression: {str(e)}'}), 500
