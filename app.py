from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
import bcrypt
import subprocess
import psutil
import time

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

# CONFIG BANCO
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'alerta_sono'

mysql = MySQL(app)

# GUARDA O PROCESSO DO PYTHON RODANDO
processo_sistema = None

def registrar_log(usuario, acao):
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO logs_sistema (usuario, acao) VALUES (%s, %s)",
        (usuario, acao)
    )
    mysql.connection.commit()
    cur.close()


# ================= ROTAS =====================

@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, senha, nome FROM usuarios WHERE email=%s", [email])
        usuario = cur.fetchone()
        cur.close()

        if usuario and bcrypt.checkpw(senha, usuario[1].encode('utf-8')):
            session['usuario'] = usuario[2]
            return redirect('/dashboard')

        return render_template("login.html", erro="Email ou senha incorretos")

    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha'].encode('utf-8')

        senha_hash = bcrypt.hashpw(senha, bcrypt.gensalt()).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
            (nome, email, senha_hash)
        )
        mysql.connection.commit()
        cur.close()

        return redirect('/login')

    return render_template("register.html")


@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template("dashboard.html", nome=session['usuario'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ========== SISTEMA DE ALERTA ==========

@app.route('/iniciar')
def iniciar_sistema():
    global processo_sistema

    if processo_sistema and processo_sistema.poll() is None:
        return jsonify({"status": "erro", "mensagem": "O sistema já está rodando!"})

    processo_sistema = subprocess.Popen(["python", "alerta_sono.py"])

    registrar_log(session['usuario'], "iniciou")

    return jsonify({"status": "ok", "mensagem": "Sistema iniciado!"})


@app.route('/parar')
def parar_sistema():
    global processo_sistema

    if processo_sistema and processo_sistema.poll() is None:
        processo_sistema.terminate()
        registrar_log(session['usuario'], "parou")
        return jsonify({"status": "ok", "mensagem": "Sistema parado com sucesso!"})
    
    return jsonify({"status": "erro", "mensagem": "O sistema não está em execução"})


@app.route('/status')
def status_sistema():
    global processo_sistema

    if processo_sistema and processo_sistema.poll() is None:
        return jsonify({"rodando": True})
    else:
        return jsonify({"rodando": False})


# ========================================

if __name__ == '__main__':
    app.run(debug=True)
