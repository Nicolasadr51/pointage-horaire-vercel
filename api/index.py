#!/usr/bin/env python3
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app

# Pour Vercel, nous devons exporter l'application comme 'handler'
def handler(request):
    return app(request.environ, request.start_response)

# Export pour Vercel
app = app
