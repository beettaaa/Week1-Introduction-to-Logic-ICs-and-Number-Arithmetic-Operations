"""NumaLogi learning portal — Flask + MariaDB backend."""
import os
import re
import secrets

import pymysql
import pymysql.cursors
from flask import Flask, g, redirect, render_template, request, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

APP_NAME = "NumaLogi"
TAGLINE = "A hands-on space for digital logic and number systems."
PROFESSOR_CODE = os.environ.get("PROFESSOR_CODE", "TUP-ACTS-PROF")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "bitgate_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "ChangeMe123!")
DB_NAME = os.environ.get("DB_NAME", "bitgate")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def connect(database=DB_NAME):
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=database, charset="utf8mb4", autocommit=False,
        cursorclass=pymysql.cursors.DictCursor, connect_timeout=5,
    )


def db():
    if "db" not in g:
        g.db = connect()
    return g.db


def query_one(sql, args=()):
    with db().cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()


@app.teardown_appcontext
def close_db(_error):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def init_db():
    """Create the application table; the database itself is created by schema.sql."""
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('student','professor') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(24)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf", "")
        expected = session.get("csrf", "")
        if not sent or not expected or not secrets.compare_digest(sent, expected):
            return "Your form session has expired. Please go back, refresh, and try again.", 400


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
            session["csrf"] = secrets.token_hex(24)
            return redirect(url_for("dashboard"))
        flash("Those details did not match an account. Check your email and password, then try again.", "error")
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
            error = "Enter a valid email address so we can identify your account."
        elif len(password) < 8:
            error = "Choose a password with at least 8 characters."
        elif len(password) > 1024:
            error = "Please choose a shorter password."
        elif password != confirm:
            error = "Your passwords do not match. Please enter them again."
        elif role == "professor" and request.form.get("code", "") != PROFESSOR_CODE:
            error = "The professor access code is incorrect. Please check with your instructor."
        if not error:
            try:
                with db().cursor() as cur:
                    cur.execute(
                        "INSERT INTO users(email,password_hash,role) VALUES(%s,%s,%s)",
                        (email, generate_password_hash(password), role),
                    )
                db().commit()
                flash("Your account is ready. Sign in to begin exploring NumaLogi.", "success")
                return redirect(url_for("login", **({"mode": "professor"} if role == "professor" else {})))
            except pymysql.err.IntegrityError:
                db().rollback()
                error = "An account with that email already exists. Try signing in instead."
            except Exception:
                db().rollback()
                app.logger.exception("Account creation failed")
                error = "We couldn't create your account right now. Please try again in a moment."
        flash(error, "error")
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

if __name__ == "__main__":
    try:
        init_db()
    except pymysql.err.OperationalError as exc:
        raise SystemExit(
            "Cannot connect to MariaDB. Start MariaDB, run schema.sql using an administrator "
            "account, then verify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD and DB_NAME.\n"
            f"Database details: {exc}"
        )
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
