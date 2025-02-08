import os
from flask import Flask, Blueprint
from database import init_db

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

    return app