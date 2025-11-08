import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

#Conectar uri de base de datos, sino no funciona
app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), unique=True, nullable=False)
    cargo = db.Column(db.String(20), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        usuario = Usuario.query.filter_by(mail=email).first()

        if usuario and check_password_hash(usuario.contraseña, password):
            session['user_id'] = usuario.id
            session['nombre'] = usuario.nombre
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email o contraseña incorrectos', 'error')
            return redirect(url_for('login'))

    return render_template('Login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        nombre = request.form['nombre']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        cargo = request.form['cargo']

        #Contraseñas iguales
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('register'))

        #Si el mail ya existe
        existing_user = Usuario.query.filter_by(mail=email).first()
        if existing_user:
            flash('El correo ya está registrado', 'error')
            return redirect(url_for('register'))

        #Encripta la contraseña del usuario en la dn
        hashed_password = generate_password_hash(password)

        nuevo_usuario = Usuario(nombre=nombre, mail=email, contraseña=hashed_password, cargo=cargo)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso. Ahora podés iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder al inicio.', 'error')
        return redirect(url_for('login'))
    return render_template('Index.html', nombre=session.get('nombre'))


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=3000)