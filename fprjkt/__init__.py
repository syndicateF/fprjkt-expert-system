import os
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
os.environ['JOBLIB_START_METHOD'] = 'loky'
from flask import Flask, Blueprint
from database import init_db
from fprjkt.main.otak import build_graph, G

syndicate = Blueprint('fprjkt',
                      __name__,
                      template_folder='main/html')

from . import routes, tombol

def create_app():
    app = Flask(__name__,
                   static_folder='../static',
                   template_folder='.')
                   
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/db_pakar'
    init_db(app)

    from . import syndicate 
    app.register_blueprint(syndicate)
    from database import db
    with app.app_context():
        db.create_all()
        build_graph()
        app.config['GRAPH'] = G
    return app