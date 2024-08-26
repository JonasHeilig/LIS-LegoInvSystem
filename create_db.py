import flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lis.db'
db = SQLAlchemy(app)


class LIS(db.Model):
    __tablename__ = 'lis'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    ls_id = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(120), unique=True, nullable=False)
    ean = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.String(120), nullable=True)
    pieces = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    owned = db.Column(db.Boolean, nullable=True, default=False)
    owned_pieces = db.Column(db.Integer, nullable=True, default=0)
    owned_list = db.Column(db.String(120), nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Collection(db.Model):
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(120), nullable=False)
    set_id = db.Column(db.Integer, db.ForeignKey('lis.id'), nullable=False)
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lis_set = db.relationship('LIS', backref=db.backref('collections', lazy=True))


with app.app_context():
    db.create_all()
    db.session.commit()
    print('Database created successfully')
    exit()
