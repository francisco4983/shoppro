from flask import Flask, render_template, session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "lojapro2024"

def get_db():
    conn = sqlite3.connect("loja.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, preco REAL,
            descricao TEXT, categoria TEXT,
            emoji TEXT, destaque INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, email TEXT UNIQUE,
            password TEXT, data_registo TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos = [
            ("Camisola Premium", 29.99, "100% algodão orgânico", "Roupa", "👕", 1),
            ("Calças Slim", 49.99, "Calças de ganga slim fit", "Roupa", "👖", 1),
            ("Ténis Runner", 79.99, "Ténis desportivos profissionais", "Calçado", "👟", 1),
            ("Boné Classic", 19.99, "Boné ajustável premium", "Acessórios", "🧢", 0),
            ("Mochila Urban", 59.99, "Mochila resistente 30L", "Acessórios", "🎒", 1),
            ("Relógio Smart", 99.99, "Relógio inteligente", "Tecnologia", "⌚", 1),
            ("Óculos Sol", 39.99, "Proteção UV400", "Acessórios", "🕶️", 0),
            ("Casaco Winter", 89.99, "Casaco impermeável", "Roupa", "🧥", 0),
        ]
        cursor.executemany("INSERT INTO produtos VALUES (NULL,?,?,?,?,?,?)", produtos)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    produtos = conn.execute("SELECT * FROM produtos").fetchall()
    destaques = conn.execute("SELECT * FROM produtos WHERE destaque=1").fetchall()
    conn.close()
    carrinho = session.get("carrinho", [])
    utilizador = session.get("utilizador")
    return render_template("index.html", produtos=produtos, destaques=destaques, total_carrinho=len(carrinho), utilizador=utilizador)

@app.route("/produto/<int:id>")
def produto(id):
    conn = get_db()
    p = conn.execute("SELECT * FROM produtos WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("produto.html", produto=p, utilizador=session.get("utilizador"), total_carrinho=len(session.get("carrinho", [])))

@app.route("/adicionar/<int:id>")
def adicionar(id):
    if not session.get("utilizador"):
        flash("Tens de fazer login para adicionar ao carrinho!")
        return redirect(url_for("login"))
    carrinho = session.get("carrinho", [])
    carrinho.append(id)
    session["carrinho"] = carrinho
    flash("Produto adicionado ao carrinho!")
    return redirect(url_for("index"))

@app.route("/carrinho")
def carrinho():
    if not session.get("utilizador"):
        return redirect(url_for("login"))
    carrinho = session.get("carrinho", [])
    conn = get_db()
    produtos_carrinho = []
    total = 0
    for id in carrinho:
        p = conn.execute("SELECT * FROM produtos WHERE id=?", (id,)).fetchone()
        if p:
            produtos_carrinho.append(p)
            total += p["preco"]
    conn.close()
    return render_template("carrinho.html", produtos=produtos_carrinho, total=total, utilizador=session.get("utilizador"), total_carrinho=len(carrinho))

@app.route("/remover/<int:index>")
def remover(index):
    carrinho = session.get("carrinho", [])
    if 0 <= index < len(carrinho):
        carrinho.pop(index)
        session["carrinho"] = carrinho
    return redirect(url_for("carrinho"))

@app.route("/registo", methods=["GET", "POST"])
def registo():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            conn = get_db()
            conn.execute("INSERT INTO utilizadores (nome, email, password) VALUES (?,?,?)", (nome, email, password))
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso! Faz login.")
            return redirect(url_for("login"))
        except:
            flash("Este email já está registado!")
    return render_template("registo.html", utilizador=None, total_carrinho=0)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM utilizadores WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["utilizador"] = user["nome"]
            session["user_id"] = user["id"]
            flash(f"Bem vindo, {user['nome']}!")
            return redirect(url_for("index"))
        flash("Email ou password incorretos!")
    return render_template("login.html", utilizador=None, total_carrinho=0)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/pesquisa")
def pesquisa():
    query = request.args.get("q", "")
    conn = get_db()
    produtos = conn.execute("SELECT * FROM produtos WHERE nome LIKE ? OR descricao LIKE ?", (f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return render_template("pesquisa.html", produtos=produtos, query=query, utilizador=session.get("utilizador"), total_carrinho=len(session.get("carrinho", [])))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)