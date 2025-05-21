# celery_app.py
from celery import Celery
import os

# This function will create a Flask app instance for the Celery worker
def create_flask_app():
    # Import the main Flask app instance or the app factory
    # To avoid circular dependencies if app.py imports tasks from here,
    # it's better to have a separate app factory function in app.py or a dedicated file.
    # For this project structure, assuming app.py can be imported carefully.
    # Ensure app.py does not try to run itself when imported by Celery.
    
    # Minimal app creation for tasks:
    from flask import Flask
    flask_app = Flask(__name__) # Use a generic name or the actual app name if known
    
    # Configure the app for SQLAlchemy and other necessary settings
    # These should match your main app.py configurations
    flask_app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_celery')
    basedir = os.path.abspath(os.path.dirname(__file__)) # This will be the root dir where celery_app.py is
    
    # Database URI - crucial for model access
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@localhost/default_db')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the warning

    # UPLOAD_FOLDER might be needed if templates reference it via app.config
    flask_app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    
    # Initialize extensions that tasks might need, e.g., SQLAlchemy
    from extensions import db
    db.init_app(flask_app)
    
    # If your app uses Blueprints and templates are in Blueprint-specific folders,
    # you might need to register them here as well for render_template to find them.
    # For now, assuming templates are in a global 'templates' folder recognized by Flask.

    return flask_app

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery(
    'tasks', # Name of the celery app (often same as the module name)
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'utils.mail_sender',
        'utils.pdf_generator'  # Added pdf_generator
    ]
)

# Store the Flask app instance on the Celery app object
# This makes it accessible in tasks via self.app.flask_app if bind=True
# or celery.flask_app
celery.flask_app = create_flask_app()


celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # You can also set CELERY_FLASK_APP if you have an app factory
    # that Celery can call, but direct assignment is also common.
)


# Optional: Example of how a task can access the app context
@celery.task(bind=True)
def dummy_task(self):
    with self.app.flask_app.app_context():
        # Now you can use Flask features that require app context
        # For example, current_app, db.session, render_template
        print(f"Running dummy_task within Flask app context: {self.app.flask_app.name}")
        return "Dummy task completed"

if __name__ == '__main__':
    # This is for starting the worker directly using `python celery_app.py worker`
    # For development, you typically run: `celery -A celery_app.celery worker -l info`
    celery.start()
