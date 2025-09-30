from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, date, timedelta
from src.models.employee import db, Employee, TimeEntry
from src.routes.auth import admin_required
import csv
import io
from sqlalchemy import func

export_bp = Blueprint('export', __name__)

@export_bp.route('/admin/export/csv', methods=['GET'])
@admin_required
def export_csv():
    """Exporter les données de pointage en CSV (admin seulement)"""
    try:
        # Paramètres de filtrage
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        employee_id = request.args.get('employee_id', type=int)
        
        # Construction de la requête
        query = db.session.query(TimeEntry, Employee).join(Employee)
        
        if start_date:
            query = query.filter(TimeEntry.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(TimeEntry.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if employee_id:
            query = query.filter(TimeEntry.employee_id == employee_id)
        
        query = query.order_by(TimeEntry.date.desc(), Employee.last_name, Employee.first_name)
        
        # Création du CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        headers = [
            'Date',
            'Numéro Employé',
            'Prénom',
            'Nom',
            'Entrée Matin',
            'Sortie Midi',
            'Entrée Après-midi',
            'Sortie Soir',
            'Heures Matin',
            'Heures Après-midi',
            'Total Heures'
        ]
        writer.writerow(headers)
        
        # Données
        for time_entry, employee in query.all():
            row = [
                time_entry.date.strftime('%Y-%m-%d'),
                employee.employee_number,
                employee.first_name,
                employee.last_name,
                time_entry.morning_in.strftime('%H:%M') if time_entry.morning_in else '',
                time_entry.lunch_out.strftime('%H:%M') if time_entry.lunch_out else '',
                time_entry.lunch_in.strftime('%H:%M') if time_entry.lunch_in else '',
                time_entry.evening_out.strftime('%H:%M') if time_entry.evening_out else '',
                f"{time_entry.morning_hours:.2f}",
                f"{time_entry.afternoon_hours:.2f}",
                f"{time_entry.total_hours:.2f}"
            ]
            writer.writerow(row)
        
        # Préparation de la réponse
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=pointages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export CSV: {str(e)}'}), 500

@export_bp.route('/admin/export/summary', methods=['GET'])
@admin_required
def export_summary():
    """Exporter un résumé des heures par employé (admin seulement)"""
    try:
        # Paramètres de filtrage
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'json')  # json ou csv
        
        if not start_date or not end_date:
            return jsonify({'error': 'Dates de début et de fin requises'}), 400
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Requête pour récupérer les totaux par employé
        query = db.session.query(
            Employee.id,
            Employee.employee_number,
            Employee.first_name,
            Employee.last_name,
            func.sum(TimeEntry.total_hours).label('total_hours'),
            func.count(TimeEntry.id).label('days_worked')
        ).join(TimeEntry).filter(
            TimeEntry.date >= start_date_obj,
            TimeEntry.date <= end_date_obj,
            Employee.is_active == True
        ).group_by(
            Employee.id,
            Employee.employee_number,
            Employee.first_name,
            Employee.last_name
        ).order_by(Employee.last_name, Employee.first_name)
        
        results = query.all()
        
        if format_type == 'csv':
            # Export CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'Numéro Employé',
                'Prénom',
                'Nom',
                'Total Heures',
                'Jours Travaillés',
                'Moyenne Heures/Jour'
            ]
            writer.writerow(headers)
            
            # Données
            for result in results:
                avg_hours = result.total_hours / result.days_worked if result.days_worked > 0 else 0
                row = [
                    result.employee_number,
                    result.first_name,
                    result.last_name,
                    f"{result.total_hours:.2f}",
                    result.days_worked,
                    f"{avg_hours:.2f}"
                ]
                writer.writerow(row)
            
            # Préparation de la réponse
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=resume_heures_{start_date}_{end_date}.csv'
            
            return response
        
        else:
            # Export JSON
            summary_data = []
            for result in results:
                avg_hours = result.total_hours / result.days_worked if result.days_worked > 0 else 0
                summary_data.append({
                    'employee_id': result.id,
                    'employee_number': result.employee_number,
                    'first_name': result.first_name,
                    'last_name': result.last_name,
                    'total_hours': round(result.total_hours, 2),
                    'days_worked': result.days_worked,
                    'average_hours_per_day': round(avg_hours, 2)
                })
            
            return jsonify({
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': summary_data,
                'total_employees': len(summary_data),
                'total_hours': sum(item['total_hours'] for item in summary_data)
            }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export du résumé: {str(e)}'}), 500

@export_bp.route('/admin/export/monthly', methods=['GET'])
@admin_required
def export_monthly():
    """Exporter les données mensuelles par employé (admin seulement)"""
    try:
        # Paramètres
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        format_type = request.args.get('format', 'json')
        
        # Calcul des dates de début et fin du mois
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Requête pour récupérer les données mensuelles
        query = db.session.query(
            Employee.id,
            Employee.employee_number,
            Employee.first_name,
            Employee.last_name,
            func.sum(TimeEntry.total_hours).label('total_hours'),
            func.count(TimeEntry.id).label('days_worked'),
            func.avg(TimeEntry.total_hours).label('avg_hours_per_day')
        ).join(TimeEntry).filter(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date,
            Employee.is_active == True
        ).group_by(
            Employee.id,
            Employee.employee_number,
            Employee.first_name,
            Employee.last_name
        ).order_by(Employee.last_name, Employee.first_name)
        
        results = query.all()
        
        if format_type == 'csv':
            # Export CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'Numéro Employé',
                'Prénom',
                'Nom',
                'Total Heures',
                'Jours Travaillés',
                'Moyenne Heures/Jour'
            ]
            writer.writerow(headers)
            
            # Données
            for result in results:
                row = [
                    result.employee_number,
                    result.first_name,
                    result.last_name,
                    f"{result.total_hours:.2f}" if result.total_hours else "0.00",
                    result.days_worked,
                    f"{result.avg_hours_per_day:.2f}" if result.avg_hours_per_day else "0.00"
                ]
                writer.writerow(row)
            
            # Préparation de la réponse
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=mensuel_{year}_{month:02d}.csv'
            
            return response
        
        else:
            # Export JSON
            monthly_data = []
            for result in results:
                monthly_data.append({
                    'employee_id': result.id,
                    'employee_number': result.employee_number,
                    'first_name': result.first_name,
                    'last_name': result.last_name,
                    'total_hours': round(result.total_hours, 2) if result.total_hours else 0.0,
                    'days_worked': result.days_worked,
                    'average_hours_per_day': round(result.avg_hours_per_day, 2) if result.avg_hours_per_day else 0.0
                })
            
            return jsonify({
                'period': {
                    'year': year,
                    'month': month,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'data': monthly_data,
                'total_employees': len(monthly_data),
                'total_hours': sum(item['total_hours'] for item in monthly_data)
            }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export mensuel: {str(e)}'}), 500
