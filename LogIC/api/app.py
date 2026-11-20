"""NumaLogi - intro to logic circuit ICs and number system conversion/arithmetic.
Run:  pip install -r requirements.txt  ->  python app.py  ->  open http://127.0.0.1:5000
Needs a running MariaDB server (see the DB_* settings below).
"""
import os, re, secrets
import pymysql
import pymysql.cursors
from flask import Flask, g, redirect, render_template, request, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

APP_NAME = "NumaLogi"
TAGLINE = "Welcome to the world of logic circuits and number conversion"
PROFESSOR_CODE = os.environ.get("PROFESSOR_CODE", "TUP-ACTS-PROF")  # change this!

# MariaDB connection settings (override with environment variables if needed)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "bitgate_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "ChangeMe123!")  # change this!
DB_NAME = os.environ.get("DB_NAME", "bitgate")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

# ---------------------------------------------------------------- database
def connect():
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
                           database=DB_NAME, charset="utf8mb4",
                           cursorclass=pymysql.cursors.DictCursor)

def db():
    if "db" not in g:
        g.db = connect()
    return g.db

def query_one(sql, args=()):
    with db().cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()

@app.teardown_appcontext
def close_db(_):
    conn = g.pop("db", None)
    if conn:
        conn.close()

def init_db():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS users(
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('student','professor') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
        conn.commit()
    finally:
        conn.close()

# ---------------------------------------------------------------- CSRF
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]

app.jinja_env.globals["csrf_token"] = csrf_token

@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf", "")
        if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
            return "Invalid form token. Go back and reload the page.", 400

# ---------------------------------------------------------------- routes
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def role_from_request():
    return "professor" if request.values.get("mode") == "professor" else "student"

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    role = role_from_request()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        row = query_one("SELECT * FROM users WHERE email=%s AND role=%s", (email, role))
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["user"] = row["email"]
            session["role"] = row["role"]
            return redirect(url_for("dashboard"))
        flash("Wrong email or password.")
    return render_template("auth.html", page="login", role=role)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    role = role_from_request()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = None
        if not EMAIL_RE.match(email):
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif role == "professor" and request.form.get("code", "") != PROFESSOR_CODE:
            error = "Invalid professor access code."
        if not error:
            try:
                with db().cursor() as cur:
                    cur.execute("INSERT INTO users(email,password_hash,role) VALUES(%s,%s,%s)",
                                (email, generate_password_hash(password), role))
                db().commit()
                flash("Account created. You can log in now.")
                return redirect(url_for("login", mode="professor" if role == "professor" else None))
            except pymysql.err.IntegrityError:
                error = "That email is already registered."
        flash(error)
    return render_template("auth.html", page="signup", role=role)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))

app.jinja_env.globals.update(app_name=APP_NAME, tagline=TAGLINE)

try:
    init_db()
except pymysql.err.OperationalError as e:
    raise SystemExit("Cannot connect to MariaDB: %s\nCheck that the server is running and the "
                     "DB_HOST / DB_USER / DB_PASSWORD / DB_NAME settings in app.py are correct." % (e,))

if __name__ == "__main__":
    app.run(debug=True)
