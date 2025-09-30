from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, date, timedelta
from src.models.employee import db, Employee, TimeEntry
from src.routes.auth import admin_required
import csv
import io
import json
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
                time_entry.date.strftime('%Y-%m-%d') if time_entry.date else '',
                employee.employee_number,
                employee.first_name,
                employee.last_name,
                time_entry.morning_in.strftime('%H:%M') if time_entry.morning_in else '',
                time_entry.lunch_out.strftime('%H:%M') if time_entry.lunch_out else '',
                time_entry.lunch_in.strftime('%H:%M') if time_entry.lunch_in else '',
                time_entry.evening_out.strftime('%H:%M') if time_entry.evening_out else '',
                f'{time_entry.morning_hours:.2f}' if time_entry.morning_hours else '0.00',
                f'{time_entry.afternoon_hours:.2f}' if time_entry.afternoon_hours else '0.00',
                f'{time_entry.total_hours:.2f}' if time_entry.total_hours else '0.00'
            ]
            writer.writerow(row)
        
        # Préparer la réponse
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=pointages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export CSV: {str(e)}'}), 500

@export_bp.route('/admin/export/summary', methods=['GET'])
@admin_required
def export_summary():
    """Exporter un résumé des heures par employé"""
    try:
        # Paramètres de filtrage
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'json')  # json ou csv
        
        # Construction de la requête
        query = db.session.query(
            Employee.employee_number,
            Employee.first_name,
            Employee.last_name,
            func.count(TimeEntry.id).label('days_worked'),
            func.sum(TimeEntry.total_hours).label('total_hours'),
            func.avg(TimeEntry.total_hours).label('average_hours')
        ).join(TimeEntry).filter(Employee.is_active == True)
        
        if start_date:
            query = query.filter(TimeEntry.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(TimeEntry.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        query = query.group_by(Employee.id).order_by(Employee.last_name, Employee.first_name)
        
        results = query.all()
        
        # Préparer les données
        summary_data = []
        for result in results:
            summary_data.append({
                'employee_number': result.employee_number,
                'first_name': result.first_name,
                'last_name': result.last_name,
                'full_name': f'{result.first_name} {result.last_name}',
                'days_worked': result.days_worked,
                'total_hours': round(float(result.total_hours or 0), 2),
                'average_hours': round(float(result.average_hours or 0), 2)
            })
        
        if format_type == 'csv':
            # Export CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'Numéro Employé',
                'Prénom',
                'Nom',
                'Jours Travaillés',
                'Total Heures',
                'Moyenne Heures/Jour'
            ]
            writer.writerow(headers)
            
            # Données
            for data in summary_data:
                row = [
                    data['employee_number'],
                    data['first_name'],
                    data['last_name'],
                    data['days_worked'],
                    data['total_hours'],
                    data['average_hours']
                ]
                writer.writerow(row)
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=resume_heures_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        else:
            # Export JSON
            return jsonify({
                'summary': summary_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'generated_at': datetime.now().isoformat()
            }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export du résumé: {str(e)}'}), 500

@export_bp.route('/admin/export/monthly', methods=['GET'])
@admin_required
def export_monthly():
    """Exporter un rapport mensuel"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        format_type = request.args.get('format', 'json')
        
        # Calculer les dates de début et fin du mois
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Requête pour les données du mois
        query = db.session.query(
            Employee.employee_number,
            Employee.first_name,
            Employee.last_name,
            func.count(TimeEntry.id).label('days_worked'),
            func.sum(TimeEntry.total_hours).label('total_hours')
        ).join(TimeEntry).filter(
            Employee.is_active == True,
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        ).group_by(Employee.id).order_by(Employee.last_name, Employee.first_name)
        
        results = query.all()
        
        # Calculer les statistiques globales
        total_employees = len(results)
        total_hours_all = sum(float(result.total_hours or 0) for result in results)
        total_days_all = sum(result.days_worked for result in results)
        
        # Préparer les données
        monthly_data = {
            'period': {
                'year': year,
                'month': month,
                'month_name': start_date.strftime('%B'),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'statistics': {
                'total_employees': total_employees,
                'total_hours': round(total_hours_all, 2),
                'total_days': total_days_all,
                'average_hours_per_employee': round(total_hours_all / total_employees if total_employees > 0 else 0, 2)
            },
            'employees': []
        }
        
        for result in results:
            monthly_data['employees'].append({
                'employee_number': result.employee_number,
                'first_name': result.first_name,
                'last_name': result.last_name,
                'full_name': f'{result.first_name} {result.last_name}',
                'days_worked': result.days_worked,
                'total_hours': round(float(result.total_hours or 0), 2),
                'average_hours_per_day': round(float(result.total_hours or 0) / result.days_worked if result.days_worked > 0 else 0, 2)
            })
        
        if format_type == 'csv':
            # Export CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-tête avec informations du mois
            writer.writerow([f'Rapport mensuel - {monthly_data["period"]["month_name"]} {year}'])
            writer.writerow([''])
            writer.writerow(['Statistiques globales'])
            writer.writerow(['Total employés', monthly_data['statistics']['total_employees']])
            writer.writerow(['Total heures', monthly_data['statistics']['total_hours']])
            writer.writerow(['Moyenne heures/employé', monthly_data['statistics']['average_hours_per_employee']])
            writer.writerow([''])
            
            # En-têtes des données employés
            headers = [
                'Numéro Employé',
                'Prénom',
                'Nom',
                'Jours Travaillés',
                'Total Heures',
                'Moyenne Heures/Jour'
            ]
            writer.writerow(headers)
            
            # Données des employés
            for emp_data in monthly_data['employees']:
                row = [
                    emp_data['employee_number'],
                    emp_data['first_name'],
                    emp_data['last_name'],
                    emp_data['days_worked'],
                    emp_data['total_hours'],
                    emp_data['average_hours_per_day']
                ]
                writer.writerow(row)
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename=rapport_mensuel_{year}_{month:02d}.csv'
            
            return response
        else:
            # Export JSON
            monthly_data['generated_at'] = datetime.now().isoformat()
            return jsonify(monthly_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export mensuel: {str(e)}'}), 500
