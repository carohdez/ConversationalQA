from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session
from sqlalchemy import func
from sqlalchemy import desc
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__, instance_relative_config=False)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.sqlite'  # para conectar directamente a sqlite
    db.init_app(app)

    # configure Session class with desired options
    Session = sessionmaker()

    # later, we create the engine
    engine = create_engine('sqlite:///mydb.sqlite', echo=True, connect_args={"check_same_thread": False})
    # associate it with our custom Session class
    Session.configure(bind=engine)

    with app.app_context():
        db.session.rollback()
        from .main import routes  # Import routes
        #db.create_all()  # Create sql tables for our data models
        #socketio.init_app(app)
        return app
