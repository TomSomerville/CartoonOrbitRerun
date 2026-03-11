from flask import Flask
from config import config

# import database objects so we can initialize
from app.database import db
# importing models ensures they're registered with Peewee
from app import models

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # initialize database (creates tables if they don't already exist)
    # using app_context in case models later use current_app
    with app.app_context():
        # connect to the database (reuse_if_open avoids errors on reload)
        db.connect(reuse_if_open=True)
        db.create_tables([
            models.User,
            # add other models here as you create them
        ])

    return app
