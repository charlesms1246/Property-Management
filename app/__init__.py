from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        # Import models here to avoid circular imports
        from app.models import User, Property, Tenant, MaintenanceRequest, RentPayment
        
        # Create all tables
        db.create_all()
        
        # Initialize views and triggers
        try:
            from app.models import init_db
            init_db()
        except Exception as e:
            print(f"Warning: Could not initialize views and triggers: {e}")

    from app.routes import auth, main, properties, tenants, maintenance
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(properties.bp)
    app.register_blueprint(tenants.bp)
    app.register_blueprint(maintenance.bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app 