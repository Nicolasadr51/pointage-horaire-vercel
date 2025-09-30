#!/usr/bin/env python3
import sys
import os
import hashlib

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import create_app
from src.models.employee import db, Employee

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_admin():
    app = create_app()
    
    with app.app_context():
        # Créer les tables
        db.create_all()
        
        # Vérifier si l'admin existe déjà
        admin = Employee.query.filter_by(employee_number='ADMIN001').first()
        if admin:
            print("✅ Administrateur déjà existant!")
            return
        
        # Créer l'administrateur
        admin_password = 'admin123'
        admin = Employee(
            employee_number='ADMIN001',
            first_name='Administrateur',
            last_name='Système',
            email='admin@pointeuse.local',
            password_hash=hash_password(admin_password),
            is_admin=True,
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Administrateur créé avec succès!")
        print("📋 Informations de connexion:")
        print(f"   Numéro d'employé: ADMIN001")
        print(f"   Mot de passe: {admin_password}")
        print(f"   Email: admin@pointeuse.local")
        print("⚠️  Pensez à changer le mot de passe après la première connexion!")

if __name__ == '__main__':
    init_admin()
