# Pointeuse Horaire

Application de gestion du temps de travail avec système de pointage pour les employés.

## 🚀 Fonctionnalités

- **Authentification sécurisée** avec rôles utilisateur (Admin/Employé)
- **Système de pointage** : 4 pointages par jour (Arrivée, Pause déjeuner, Retour déjeuner, Départ)
- **Tableau de bord administrateur** avec statistiques en temps réel
- **Gestion complète des employés** (création, modification, recherche)
- **Module d'exports** pour rapports et analyses (CSV, JSON)
- **Interface responsive** et moderne

## 🛠️ Technologies

### Backend
- **Flask** - Framework web Python
- **SQLAlchemy** - ORM pour la base de données
- **SQLite** - Base de données
- **Flask-CORS** - Gestion des CORS
- **Hashlib** - Hachage des mots de passe

### Frontend
- **React** - Framework JavaScript
- **Vite** - Build tool
- **Tailwind CSS** - Framework CSS
- **Lucide React** - Icônes

## 📁 Structure du projet

```
pointage-app/
├── backend/                 # API Flask
│   ├── src/
│   │   ├── models/         # Modèles de données
│   │   └── routes/         # Routes API
│   ├── static/             # Fichiers statiques du frontend
│   ├── database/           # Base de données SQLite
│   ├── app.py             # Application principale
│   ├── requirements.txt   # Dépendances Python
│   └── vercel.json        # Configuration Vercel
├── frontend-new/           # Application React
│   ├── src/
│   │   ├── components/    # Composants React
│   │   └── App.jsx        # Composant principal
│   ├── package.json       # Dépendances Node.js
│   └── vite.config.js     # Configuration Vite
└── docs/                  # Documentation
```

## 🚀 Installation et déploiement

### Prérequis
- Python 3.11+
- Node.js 18+
- pnpm

### Installation locale

1. **Cloner le repository**
```bash
git clone https://github.com/Nicolasadr51/pointage-horaire.git
cd pointage-horaire
```

2. **Backend**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

3. **Frontend** (pour développement)
```bash
cd frontend-new
pnpm install
pnpm run dev
```

### Déploiement sur Vercel

L'application est configurée pour être déployée sur Vercel avec le backend et frontend intégrés.

1. Connecter le repository GitHub à Vercel
2. Configurer le répertoire racine sur `/backend`
3. Déployer

## 🔑 Identifiants par défaut

- **Administrateur** : `ADMIN001` / `admin123`

## 📊 API Endpoints

### Authentification
- `POST /api/auth/login` - Connexion
- `GET /api/auth/me` - Vérification du statut
- `POST /api/auth/logout` - Déconnexion

### Employés
- `GET /api/employees` - Liste des employés
- `POST /api/employees` - Créer un employé
- `PUT /api/employees/{id}` - Modifier un employé
- `DELETE /api/employees/{id}` - Supprimer un employé

### Pointages
- `GET /api/timeentries` - Liste des pointages
- `POST /api/timeentries` - Créer un pointage
- `GET /api/timeentries/employee/{id}` - Pointages d'un employé

### Exports
- `GET /api/export/csv` - Export CSV
- `GET /api/export/json` - Export JSON

## 🔧 Configuration

### Variables d'environnement
- `SECRET_KEY` - Clé secrète Flask (optionnel, valeur par défaut fournie)

### Base de données
La base de données SQLite est créée automatiquement au premier démarrage avec un utilisateur administrateur par défaut.

## 📝 Licence

Ce projet est sous licence MIT.

## 👥 Contributeurs

- Développé avec l'assistance de Manus AI
