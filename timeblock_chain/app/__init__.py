# app/__init__.py
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from flask_cors import CORS

def create_app():
    # Initialize Firebase Admin
    cred = credentials.Certificate("/Users/conceptualdanny/Desktop/Everything/MetaPrograms/MetaIdeas/Obisverse/timeblock_chain/app/services/service_account.json")
    firebase_admin.initialize_app(cred)

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for /api routes"

    # Initialize Firestore DB
    db = firestore.client()

    # Initialize TimeblockService with the Firestore client
    from .services.timeblock_service import TimeblockService
    app.timeblock_service = TimeblockService(db)

    # Register routes
    from .routes import timeblock_routes
    app.register_blueprint(timeblock_routes.bp)

    return app

