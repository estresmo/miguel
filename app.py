import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'akuma'
mysql = MySQL(app)
app.secret_key = b'192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
app.config['TEMPLATES_AUTO_RELOAD'] = True
ALLOWED_EXTENSIONS = set([ 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename:str):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def inicio():
    return render_template('Inicio.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s AND clave = %s', (username, password))
        account = cur.fetchone()
        if account:
            session['user_id'] = account[0]
            session['nombre'] = account[1]
            session['apellido'] = account[2]
            session['correo'] = account[3]
            return redirect(url_for('admin_artistas'))
        else:
            msg = 'Usuario y contraseña incorrecto'
    return render_template('inicio', msg=msg)


@app.route('/logout')
def logout(): 
    session.clear()
    return redirect(url_for('inicio'))


@app.route('/registro/', methods=['GET', 'POST'])
def registro():
    msg = ''
    if request.method == 'POST':
        correo = request.form['username']
        clave = request.form['password']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cur = mysql.connection.cursor()
        cur.execute('SELECT id from usuarios WHERE correo=%s', [correo])
        cur.fetchall()
        rc = cur.rowcount
        if rc > 0:
            msg = "El correo ya está registrado"
        else:
            cur.execute('INSERT INTO usuarios(nombre, apellido, correo, clave) VALUES(%s,%s,%s,%s);',
                        (nombre, apellido, correo, clave))
            mysql.connection.commit()
            msg = 'Usuario creado correctamente'
    
    return render_template('registro.html', msg=msg)


@app.route("/artistas")
def artistas():
    return render_template('Artistas.html')


@app.route("/contactos")
def contactos():
    return render_template('Contactos.html')


@app.route("/nosotros")
def nosotros():
    return render_template('Nosotros.html')


@app.route("/testimonios")
def testimonios():
    return render_template('Testimonios.html')


@app.route("/akuma_clothing")
def akuma_cloting():
    return render_template('clothing/inicio.html', **{'carrito': True})

@app.route("/admin/artistas", methods=['GET', 'POST'])
def admin_artistas():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        artista_id = request.form['artista-id']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        especialidad = request.form['especialidad']
        facebook = request.form['facebook']
        instagram = request.form['instagram']
        filename = ""
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename == '':
                flash('No selected file')
            elif foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                fullFilename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(fullFilename)
        if artista_id == "":
            cur.execute('INSERT INTO artistas(nombre, apellido, especialidad, facebook, instagram, foto) VALUES(%s,%s,%s,%s,%s,%s);',
                    (nombre, apellido, especialidad, facebook, instagram, filename))
            registro = "Ha creado un artista"
            cur.execute(f"""INSERT INTO bitacora(usuario,registro) VALUES('{session['correo']}','{registro}')""")
        else:
            cur.execute('''UPDATE artistas SET nombre=%s, apellido=%s, especialidad=%s, facebook=%s, instagram=%s, foto=%s 
            WHERE id=%s;''' ,(nombre, apellido, especialidad, facebook, instagram, filename, artista_id))
            registro = "Ha editado un artista"
            cur.execute(f"""INSERT INTO bitacora(usuario,registro) VALUES('{session['correo']}','{registro}')""")
        mysql.connection.commit()
        return redirect(request.url)
    else:
        eliminar = request.args.get("eliminar")
        if eliminar is not None:
            registro = "Ha eliminado un artista"
            cur.execute(f"""INSERT INTO bitacora(usuario,registro) VALUES('{session['correo']}','{registro}')""")
            cur.execute('DELETE FROM artistas WHERE id=%s',eliminar)
            mysql.connection.commit()
    cur.execute('SELECT * FROM artistas')
    artistas = cur.fetchall()
    print(artistas)
    return render_template('admin/artistas.html',artistas=artistas)

@app.route("/admin/producto")
def admin_producto():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        producto_id = request.form['producto-id']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        filename = ""
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename == '':
                flash('No selected file')
            elif foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                fullFilename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(fullFilename)
        if producto_id == "":
            cur.execute('INSERT INTO productos(nombre, descripcion, precio, foto) VALUES(%s,%s,%s,%s,%s);',
                    (nombre, descripcion, precio, filename))
        else:
            cur.execute('''UPDATE productos SET nombre=%s, descripcion=%s, precio=%s, foto=%s 
            WHERE id=%s;''' ,(nombre, descripcion, precio, filename, producto_id))
        mysql.connection.commit()
        return redirect(request.url)
    else:
        eliminar = request.args.get("eliminar")
        if eliminar is not None:
            cur.execute('DELETE FROM productos WHERE id=%s',eliminar)
            mysql.connection.commit()
    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()
    print(productos)
    return render_template('admin/producto.html')


@app.route("/admin/galeria")
def admin_galeria():
    return render_template('admin/galeria.html')


@app.route("/admin/bitacora")
def admin_bitacora():
    context = {}
    desde = request.args.get("desde",None)
    hasta = request.args.get("hasta",None)
    if  desde is not None:
        cur = mysql.connection.cursor()
        desde += " 0:00:00"
        hasta += " 0:00:00"     
        cur.execute(f"SELECT * FROM bitacora WHERE fecha_registro between '{desde}' and '{hasta}'")
        bitacora = cur.fetchall()
        context['bitacora'] = bitacora
    return render_template('admin/bitacora.html',**context)

if __name__ == '__main__':
    app.debug = True
    app.run()