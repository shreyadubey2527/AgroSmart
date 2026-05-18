from flask import Flask, request, session
from flask_babel import Babel,_
import os
from .models.db import close_db, init_db
from .routes.main_routes import main
from .routes.auth_routes import auth
from .routes.password import password
from .routes.prediction_routes import predict
from dotenv import load_dotenv

load_dotenv()

babel = Babel()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'

    # Flask-Babel locale selector
    def get_locale():
        # 1. Check URL parameter
        lang = request.args.get('lang')
        if lang in ['en', 'hi', 'mr']:
            session['lang'] = lang
            return lang
        
        # 2. Check session
        if 'lang' in session:
            return session['lang']
        
        # 3. Check browser default
        return request.accept_languages.best_match(['en', 'hi', 'mr']) or 'en'

    babel.init_app(app, locale_selector=get_locale)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Database teardown
    app.teardown_appcontext(close_db)

    # Initialize database
    with app.app_context():
        init_db()

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(password)
    app.register_blueprint(predict)

    return app