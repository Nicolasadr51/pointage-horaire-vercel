from flask import Blueprint, request, jsonify, session
from datetime import datetime, date, time
from src.models.employee import db, Employee, TimeEntry
from src.routes.auth import login_required, admin_required

timeentry_bp = Blueprint('timeentry', __name__)

@timeentry_bp.route('/punch', methods=['POST'])
@login_required
def punch_time():
    """Enregistrer un pointage"""
    try:
        data = request.get_json()
        punch_type = data.get('type')  # morning_in, lunch_out, lunch_in, evening_out
        
        if punch_type not in ['morning_in', 'lunch_out', 'lunch_in', 'evening_out']:
            return jsonify({'error': 'Type de pointage invalide'}), 400
        
        employee_id = session['employee_id']
        today = date.today()
        current_time = datetime.now().time()
        
        # Rechercher ou créer l'entrée du jour
        time_entry = TimeEntry.query.filter_by(
            employee_id=employee_id,
            date=today
        ).first()
        
        if not time_entry:
            time_entry = TimeEntry(
                employee_id=employee_id,
                date=today
            )
            db.session.add(time_entry)
        
        # Vérifier la logique des pointages
        if punch_type == 'lunch_out' and not time_entry.morning_in:
            return jsonify({'error': 'Vous devez d\'abord pointer votre arrivée du matin'}), 400
        elif punch_type == 'lunch_in' and not time_entry.lunch_out:
            return jsonify({'error': 'Vous devez d\'abord pointer votre sortie déjeuner'}), 400
        elif punch_type == 'evening_out' and not time_entry.lunch_in:
            return jsonify({'error': 'Vous devez d\'abord pointer votre retour de déjeuner'}), 400
        
        # Vérifier si le pointage n'a pas déjà été fait
        if getattr(time_entry, punch_type):
            return jsonify({'error': 'Ce pointage a déjà été effectué'}), 400
        
        # Mettre à jour le pointage
        setattr(time_entry, punch_type, current_time)
        
        # Recalculer les heures
        time_entry.calculate_hours()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Pointage {punch_type} enregistré',
            'time_entry': time_entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors du pointage: {str(e)}'}), 500

@timeentry_bp.route('/today', methods=['GET'])
@login_required
def get_today_entry():
    """Récupérer le pointage du jour pour l'employé connecté"""
    try:
        employee_id = session['employee_id']
        today = date.today()
        
        time_entry = TimeEntry.query.filter_by(
            employee_id=employee_id,
            date=today
        ).first()
        
        if not time_entry:
            return jsonify({'time_entry': None}), 200
        
        return jsonify({'time_entry': time_entry.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération des données: {str(e)}'}), 500

@timeentry_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """Récupérer l'historique des pointages de l'employé"""
    try:
        employee_id = session['employee_id']
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limiter le nombre d'éléments par page
        per_page = min(per_page, 100)
        
        entries = TimeEntry.query.filter_by(employee_id=employee_id)\
                                .order_by(TimeEntry.date.desc())\
                                .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries.items],
            'total': entries.total,
            'pages': entries.pages,
            'current_page': entries.page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération de l\'historique: {str(e)}'}), 500

@timeentry_bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """Récupérer un résumé des heures travaillées"""
    try:
        employee_id = session['employee_id']
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = TimeEntry.query.filter_by(employee_id=employee_id)
        
        if start_date:
            query = query.filter(TimeEntry.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(TimeEntry.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        entries = query.all()
        
        total_hours = sum(entry.total_hours for entry in entries)
        total_days = len(entries)
        average_hours = total_hours / total_days if total_days > 0 else 0
        
        return jsonify({
            'total_hours': round(total_hours, 2),
            'total_days': total_days,
            'average_hours': round(average_hours, 2),
            'entries_count': total_days
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors du calcul du résumé: {str(e)}'}), 500

# Routes administrateur

@timeentry_bp.route('/admin/entries', methods=['GET'])
@admin_required
def get_all_entries():
    """Récupérer tous les pointages (admin seulement)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Limiter le nombre d'éléments par page
        per_page = min(per_page, 100)
        
        query = db.session.query(TimeEntry).join(Employee)
        
        if employee_id:
            query = query.filter(TimeEntry.employee_id == employee_id)
        if start_date:
            query = query.filter(TimeEntry.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(TimeEntry.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        query = query.order_by(TimeEntry.date.desc(), Employee.last_name, Employee.first_name)
        
        entries = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries.items],
            'total': entries.total,
            'pages': entries.pages,
            'current_page': entries.page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération des pointages: {str(e)}'}), 500

@timeentry_bp.route('/admin/entries/<int:entry_id>', methods=['PUT'])
@admin_required
def update_entry(entry_id):
    """Modifier un pointage (admin seulement)"""
    try:
        data = request.get_json()
        
        entry = TimeEntry.query.get_or_404(entry_id)
        
        # Mettre à jour les champs de temps
        time_fields = ['morning_in', 'lunch_out', 'lunch_in', 'evening_out']
        for field in time_fields:
            if field in data and data[field]:
                try:
                    time_value = datetime.strptime(data[field], '%H:%M').time()
                    setattr(entry, field, time_value)
                except ValueError:
                    return jsonify({'error': f'Format d\'heure invalide pour {field}'}), 400
            elif field in data and data[field] is None:
                setattr(entry, field, None)
        
        # Recalculer les heures
        entry.calculate_hours()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pointage mis à jour avec succès',
            'entry': entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500
