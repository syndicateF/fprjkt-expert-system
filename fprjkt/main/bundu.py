from flask import request, session, flash
from database.db_pakar import User, Riwayat, Conflict, Example, Solution, Relation
from database import db

def login(username, password):
    try:

        kawan = User.query.filter_by(username=username).first()
        if kawan and kawan.password == password:
            session['login'] = kawan.id
            session['nama_lengkap'] = f"{kawan.nama_depan} {kawan.nama_belakang}"
            return True
        else:
            flash('Username atau password salah', 'g')
    except Exception as e:
        flash(f"login: {str(e)}", 'g')
    return False

def username_exists(username):
    return User.query.filter_by(username=username).first() is not None

def registrasi(regis_form):
    nama_depan = regis_form.get('nama_depan')
    nama_belakang = regis_form.get('nama_belakang')
    username = regis_form.get('username')
    password = regis_form.get('password')
    email = regis_form.get('email')

    return {
        'nama_depan': nama_depan,
        'nama_belakang': nama_belakang,
        'username': username,
        'password': password,
        'email': email
    }
    
def simpan_riwayat(masalah, solusi, kepastian, user_id):
    hasil_riwayat = Riwayat(masalah=masalah,
                            solusi=solusi,
                            kepastian=kepastian,
                            user_id=user_id)
    db.session.add(hasil_riwayat)
    db.session.commit()