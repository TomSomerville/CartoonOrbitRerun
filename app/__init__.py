import os
from flask import Flask
from config import config

# import database objects so we can initialize
from app.database import db
# importing models ensures they're registered with Peewee
from app import models

def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Inject ad GIF list into all templates
    ads_dir = os.path.join(app.static_folder, 'ads')
    @app.context_processor
    def inject_ad_gifs():
        gifs = []
        if os.path.isdir(ads_dir):
            gifs = [f'/static/ads/{f}' for f in sorted(os.listdir(ads_dir))
                    if f.lower().endswith('.gif')]
        return {'ad_gifs': gifs}

    # Inject eventbottom GIF list into all templates
    eventbottom_dir = os.path.join(app.static_folder, 'eventbottom')
    @app.context_processor
    def inject_eventbottom_gifs():
        gifs = []
        if os.path.isdir(eventbottom_dir):
            gifs = [f'/static/eventbottom/{f}' for f in sorted(os.listdir(eventbottom_dir))
                    if f.lower().endswith('.gif')]
        return {'eventbottom_gifs': gifs}

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
