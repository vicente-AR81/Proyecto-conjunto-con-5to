import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

#Conectar uri de base de datos, sino no funciona
app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), unique=True, nullable=False)
    cargo = db.Column(db.String(20), nullable=False)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    imagen = db.Column(db.String(255), nullable=True)

    items = db.relationship("VentaItem", backref="venta", cascade="all, delete-orphan")

class VentaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    producto = db.relationship("Producto")

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

@app.route('/stock')
def stock():
    productos = Producto.query.all()
    return render_template('Stock.html', productos=productos)

@app.route('/agregar_stock', methods=['GET', 'POST'])
def agregar_stock():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        precio = request.form['precio']

        nuevo = Producto(nombre=nombre, descripcion=descripcion, stock=stock, precio=precio)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('stock'))

    return render_template('Formulario_Stock.html')

@app.route('/proveedores')
def proveedores():
    return render_template('Proveedores.html')

@app.route('/ventas')
def ventas():
    ventas = Venta.query.all()
    return render_template('Ventas.html', ventas=ventas)


@app.route('/agregar_venta', methods=['GET', 'POST'])
def agregar_venta():
    productos = Producto.query.all()

    if request.method == 'POST':
        titulo = request.form['titulo']

        imagen_file = request.files.get('imagen')
        imagen_path = None

        if imagen_file and imagen_file.filename != "":
            filename = secure_filename(imagen_file.filename)

            # Ruta física donde se guarda
            ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(ruta_archivo)

            # Ruta relativa para mostrar en HTML
            imagen_path = f"uploads/{filename}"

        venta = Venta(
            titulo=titulo,
            imagen=imagen_path
        )
        db.session.add(venta)
        db.session.commit()

        # Registrar productos vendidos
        for p in productos:
            cantidad = request.form.get(f"cantidad_{p.id}")
            if cantidad and int(cantidad) > 0:
                cantidad = int(cantidad)

                item = VentaItem(
                    venta_id=venta.id,
                    producto_id=p.id,
                    cantidad=cantidad,
                    precio_unitario=p.precio
                )
                db.session.add(item)

                p.stock -= cantidad

        db.session.commit()
        return redirect(url_for('ventas'))

    return render_template('Agregar_Venta.html', productos=productos)


@app.route('/gastos')
def gastos():
    return render_template('Gastos.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=3000)