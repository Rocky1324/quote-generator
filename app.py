from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, session, redirect, render_template, request, url_for, flash
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "My_secret_key"

# TAbleau d'authentification
def db_init():
    connect = sqlite3.connect("user.db")
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS user(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT,
                   password TEXT
                   )
                   """)
    connect.commit()
    cursor.close()

# Tableau favorite
def fav_init():
    connect = sqlite3.connect("favorite.db")
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS favorites(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   Author TEXT,
                   Quote TEXT,
                   user_id INTEGER,
                   FOREIGN KEY (user_id) REFERENCES user(id)
                   )
                   """)

db_init()
fav_init()

# page d'acceuil
@app.route("/", methods = ["GET", "POST"])
def home():
    username =  session.get("username")
    if username:
        return redirect(url_for("profil"))
    return render_template("index.html")

# Page d'inscription
@app.route("/regist", methods = ["GET", "POST"])
def regist():
    if request.method == "POST":
        username = request.form.get("username")
        connect = sqlite3.connect("user.db")
        cursor = connect.cursor()
        # verifier que le username n'est pas deja utilise
        cursor.execute("SELECT username FROM user")
        identify = [{"name": r[0]}for r in cursor.fetchall()]
        for identity in identify:
            if identity["name"] == username:
                return "username deja utilise"
        session["username"] = username
        password = request.form.get("password")
        ash = generate_password_hash(password)
        cursor.execute("INSERT INTO user(username, password) VALUES(?, ?)", (username, ash,))
        connect.commit()
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        session["user_id"] = user_id
        cursor.close()
        flash("tu es connecte", "succes")
        return render_template("profil.html", username = username)
    return render_template("regist.html")

# Page de connection
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        connect = sqlite3.connect("user.db")
        cursor = connect.cursor()
        cursor.execute("SELECT password FROM user WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[0], password):
            cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
            user_id = cursor.fetchone()[0]
            cursor.close()
            session["user_id"] = user_id
            session["username"] = username  
            flash("Tu es connecte", "succes")
            return redirect(url_for("profil"))
        flash("Mot de passe ou usrname incorrecte", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

# Page de deconnection
@app.route("/logout", methods = ["GET", "POST"])
def logout():
    username = session.get("username")
    if username is None:
        redirect(url_for("login"))
    if request.method == "POST":
        session.clear()
        return render_template("index.html")
    return render_template("logout.html")

# Page de profil
@app.route("/profil", methods = ["GET", "POST"])
def profil():
    username = session.get("username")
    if username is None:
        return render_template("login.html")
    return render_template("profil.html", username = username)

# Page & initiation des categories
@app.route("/categorie", methods = ["GET", "POST"])
def categorie():
    username = session.get("username")
    if username is None:
        return redirect(url_for("login"))
    connect = sqlite3.connect("quotes.db")
    cursor = connect.cursor()
    cursor.execute("SELECT name FROM Category")
    category = [{"name": r[0]}for r in cursor.fetchall()]
    cursor.close()
    return render_template("category.html", category = category)

# Page des citations
@app.route("/quotes", methods = ["GET", "POST"])
def quote():
    username =  session.get("username")
    if username is None:
        return redirect(url_for("login"))
    category = request.form.get("category") or session.get("Categorie")
    session["Categorie"] = category
    connect = sqlite3.connect("quotes.db")
    cursor = connect.cursor()
    cursor.execute("SELECT Authors, Quote, id FROM Quotes WHERE Category = ?", (session["Categorie"],))
    quotes = [{"Authors": r[0], "Quote": r[1], "id": r[2]}for r in cursor.fetchall()]
    cursor.close()
    selected = random.choice(quotes)
    return render_template("quotes.html", selected = selected)


# Ajout aux tableaux des favorite
@app.route("/favorite/<int:id>", methods = ["GET", "POST"])
def add_favorite(id):
    username =  session.get("username")
    if username is None:
        return redirect(url_for("login"))
    if request.method == "POST":
        connect = sqlite3.connect("quotes.db")
        cursor = connect.cursor()
        cursor.execute("SELECT Authors, Quote FROM Quotes WHERE id = ?", (id,))
        favorite = [{"Authors": r[0], "Quote": r[1]}for r in cursor.fetchall()]
        cursor.close()


        fav = favorite
        conn = sqlite3.connect("favorite.db")
        curs = conn.cursor()
        curs.execute("SELECT 1 FROM favorites WHERE user_id = ? AND Quote = ?", (session["user_id"], fav[0]["Quote"],))
        result = curs.fetchone()
        if result:
            flash("Cette citation est deja dans vos favorits", "Warning")
            return redirect(url_for("quote"))
        curs.execute("INSERT INTO favorites (Author, Quote, user_id) VALUES (?, ?, ?)", (fav[0]["Authors"], fav[0]["Quote"], session["user_id"],))
        conn.commit()
        curs.close()
        flash("La citation a ete ajoutee aux favorits")
        return redirect(url_for("quote"))
    return render_template("favorite.html")

# Page des favorits
@app.route("/favorite", methods = ["GET", "POST"])
def favorite():
    username = session.get("username")
    if username is None:
        return redirect(url_for("login"))
    connect = sqlite3.connect("favorite.db")
    cursor = connect.cursor()
    cursor.execute("SELECT id, Author, Quote FROM favorites WHERE user_id = ?", (session["user_id"],))
    favorit = [{"id": r[0], "Author": r[1], "Quote": r[2]}for r in cursor.fetchall()]
    cursor.close()
    return render_template("favorite.html", favorit = favorit)

# Enlever des favorits
@app.route("/delete/<int:id>", methods = ["GET", "POST"])
def delete(id):
    if request.method == "POST":
        connect = sqlite3.connect("favorite.db")
        cursor = connect.cursor()
        cursor.execute("DELETE FROM favorites WHERE id = ?", (id,))
        connect.commit()
        cursor.close()
        return redirect(url_for("favorite"))
    return redirect(url_for("favorite"))
