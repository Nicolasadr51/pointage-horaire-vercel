            time_entry = TimeEntry(
                employee_id=employee_id,
                date=today
            )
            db.session.add(time_entry)
        
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
