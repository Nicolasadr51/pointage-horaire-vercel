#!/usr/bin/env python3
"""
Script d'initialisation de l'administrateur par défaut
"""
import os
import sys
import bcrypt

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(__file__))

from src.main import create_app
from src.models.employee import db, Employee

def init_admin():
    """Créer l'administrateur par défaut"""
    app = create_app()
    
    with app.app_context():
        # Vérifier si l'admin existe déjà
        admin = Employee.query.filter_by(employee_number='ADMIN001').first()
        
        if admin:
            print("L'administrateur ADMIN001 existe déjà.")
            print(f"Nom: {admin.get_full_name()}")
            print(f"Email: {admin.email}")
            print(f"Statut: {'Actif' if admin.is_active else 'Inactif'}")
            return
        
        # Créer l'administrateur
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin = Employee(
            employee_number='ADMIN001',
            first_name='Administrateur',
            last_name='Système',
            email='admin@pointeuse.local',
            password_hash=password_hash,
            is_admin=True,
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Administrateur créé avec succès!")
        print("📋 Informations de connexion:")
        print(f"   Numéro d'employé: {admin.employee_number}")
        print(f"   Mot de passe: {password}")
        print(f"   Email: {admin.email}")
        print("\n⚠️  Pensez à changer le mot de passe après la première connexion!")

if __name__ == '__main__':
    init_admin()
