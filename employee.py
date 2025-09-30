from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation avec les pointages
    time_entries = db.relationship('TimeEntry', backref='employee', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Employee {self.employee_number}: {self.first_name} {self.last_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'employee_number': self.employee_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # Les 4 créneaux de pointage
    morning_in = db.Column(db.Time, nullable=True)    # Entrée du matin
    lunch_out = db.Column(db.Time, nullable=True)     # Sortie du midi
    lunch_in = db.Column(db.Time, nullable=True)      # Entrée après-midi
    evening_out = db.Column(db.Time, nullable=True)   # Sortie du soir
    
    # Heures calculées
    morning_hours = db.Column(db.Float, default=0.0)  # Heures du matin
    afternoon_hours = db.Column(db.Float, default=0.0) # Heures de l'après-midi
    total_hours = db.Column(db.Float, default=0.0)    # Total journalier
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour optimiser les requêtes
    __table_args__ = (
        db.Index('idx_employee_date', 'employee_id', 'date'),
    )

    def __repr__(self):
        return f'<TimeEntry {self.employee_id} - {self.date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat() if self.date else None,
            'morning_in': self.morning_in.strftime('%H:%M') if self.morning_in else None,
            'lunch_out': self.lunch_out.strftime('%H:%M') if self.lunch_out else None,
            'lunch_in': self.lunch_in.strftime('%H:%M') if self.lunch_in else None,
            'evening_out': self.evening_out.strftime('%H:%M') if self.evening_out else None,
            'morning_hours': self.morning_hours,
            'afternoon_hours': self.afternoon_hours,
            'total_hours': self.total_hours,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_hours(self):
        """Calcule les heures travaillées pour cette entrée"""
        self.morning_hours = 0.0
        self.afternoon_hours = 0.0
        
        # Calcul des heures du matin
        if self.morning_in and self.lunch_out:
            morning_delta = datetime.combine(self.date, self.lunch_out) - datetime.combine(self.date, self.morning_in)
            self.morning_hours = morning_delta.total_seconds() / 3600
        
        # Calcul des heures de l'après-midi
        if self.lunch_in and self.evening_out:
            afternoon_delta = datetime.combine(self.date, self.evening_out) - datetime.combine(self.date, self.lunch_in)
            self.afternoon_hours = afternoon_delta.total_seconds() / 3600
        
        # Total journalier
        self.total_hours = self.morning_hours + self.afternoon_hours
        
        return self.total_hours
