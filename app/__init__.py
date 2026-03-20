import os
from flask import Flask, request
from config import config

_IMAGE_EXTS = ('.gif', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico')
_IMAGE_CACHE_SECONDS = 7 * 24 * 60 * 60  # 7 days

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

    # Long-lived cache headers for image assets so browsers never re-validate
    # within the 7-day window — no conditional GETs, no 304s, zero server contact.
    @app.after_request
    def set_image_cache_headers(response):
        path = request.path.lower()
        if path.endswith(_IMAGE_EXTS) and (
            path.startswith('/static/') or
            path.startswith('/ctoon-img/') or
            path.startswith('/czone-bg/')
        ):
            response.cache_control.public = True
            response.cache_control.max_age = _IMAGE_CACHE_SECONDS
            response.cache_control.no_cache = None
            response.cache_control.no_store = None
        return response

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
            models.CToon,
            models.UserCToon,
            models.CZone,
            models.CZoneItem,
        ], safe=True)

    return app
