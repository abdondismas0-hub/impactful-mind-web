# config.py

import os

# Ficha key hii!
SECRET_KEY = os.environ.get('SECRET_KEY') or 'hii-ni-secret-key-ngumu-sana-ya-kuficha'

# Configuration ya Database (SQLite inatosha kuanzia)
class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mahali pa kuhifadhi PDF (kwa mfano)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
