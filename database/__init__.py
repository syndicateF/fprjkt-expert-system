from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
banjir = Migrate()

def init_db(app):
    db.init_app(app)
    banjir.init_app(app, db)
