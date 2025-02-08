from database import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    nama_depan = db.Column(db.String(100), unique=False, nullable=False)
    nama_belakang = db.Column(db.String(100), unique=False, nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    masalah = db.relationship('Riwayat', backref='user', lazy=True)

class Riwayat(db.Model):
    __tablename__ = 'riwayat'
    id = db.Column(db.Integer, primary_key=True)
    masalah = db.Column(db.Text, nullable=False)
    solusi = db.Column(db.Text, nullable=False)
    kepastian = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Conflict(db.Model):
    __tablename__ = 'conflicts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    saran = db.Column(db.Text, nullable=True)

    examples = db.relationship('Example', backref='conflict', lazy=True, cascade="all, delete-orphan")
    solutions = db.relationship('Solution', backref='conflict', lazy=True, cascade="all, delete-orphan")
    relations = db.relationship('Relation', backref='conflict', lazy=True, cascade="all, delete-orphan")

class Example(db.Model):
    __tablename__ = 'examples'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    conflict_id = db.Column(db.Integer, db.ForeignKey('conflicts.id'), nullable=False)

class Solution(db.Model):
    __tablename__ = 'solutions'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    conflict_id = db.Column(db.Integer, db.ForeignKey('conflicts.id'), nullable=False)

class Relation(db.Model):
    __tablename__ = 'relations'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    conflict_id = db.Column(db.Integer, db.ForeignKey('conflicts.id'), nullable=False)
