"""LogicLab Flask + MySQL server.

Run with: python app.py
Then open: http://127.0.0.1:5000
"""
from __future__ import annotations

import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from random import randint, shuffle
from typing import Any

import pymysql
from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config

ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = ROOT / "api" / "private" / "questions.json"
LESSONS = {
    "bases", "division", "expansion", "grouping", "addition", "multiply",
    "signed", "overflow", "levels", "gates", "pinouts", "adder",
}
MODULES = {"all", "conversions", "arithmetic", "ics"}

app = Flask(__name__, static_folder="assets", static_url_path="/assets")
app.config.from_object(Config)


def db() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def csrf() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(32)
    return session["csrf"]


def api(data: dict[str, Any], status: int = 200):
    response = jsonify(data)
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def error(message: str, status: int = 400):
    return api({"error": message, "csrf": csrf()}, status)


def read_body() -> tuple[dict[str, Any] | None, Any | None]:
    if request.content_length and request.content_length > 24000:
        return None, error("Request too large.", 413)
    if not secrets.compare_digest(csrf(), request.headers.get("X-CSRF-Token", "")):
        return None, error("Session expired. Refresh the page and try again.", 403)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, error("Invalid request.")
    return body, None


def get_user() -> tuple[dict[str, Any] | None, Any | None]:
    user_id = session.get("user_id")
    if not user_id:
        return None, error("Please log in to save your progress.", 401)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, email FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    if not user:
        session.clear()
        return None, error("Please log in again.", 401)
    return user, None


def iso(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def normalize(value: str, numeric: bool) -> str:
    value = value.strip()
    if not numeric:
        return value
    value = value.upper().lstrip("0")
    return value or "0"


def complete_result(row: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(row["result"])
    result.update({"id": row["id"], "moduleId": row["module_id"], "completedAt": iso(row["completed_at"])})
    return result


def load_questions(module: str) -> list[dict[str, Any]]:
    bank = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    decimal = randint(10, 63)
    hex_value = randint(17, 96)
    add_a, add_b = randint(2, 7), randint(1, 7)
    for question in bank:
        if question["id"] == "c1":
            question["prompt"] = f"Convert {decimal}₁₀ to binary. Enter digits only."
            question["answer"] = bin(decimal)[2:]
            question["explanation"] = f"Divide {decimal} repeatedly by 2; read the remainders bottom to top: {bin(decimal)[2:]}₂."
        elif question["id"] == "c2":
            hex_text = f"{hex_value:X}"
            question["prompt"] = f"Convert {hex_text}₁₆ to decimal."
            question["answer"] = str(hex_value)
            question["explanation"] = f"{hex_text}₁₆ = {hex_value // 16} × 16 + {hex_value % 16} = {hex_value}."
        elif question["id"] == "a1":
            question["prompt"] = f"Add {add_a:b}₂ + {add_b:b}₂. Enter the full binary result."
            question["answer"] = f"{add_a + add_b:b}"
            question["explanation"] = f"{add_a} + {add_b} = {add_a + add_b}, which is {add_a + add_b:b}₂."
    questions: list[dict[str, Any]] = []
    for topic in ("conversions", "arithmetic", "ics"):
        if module != "all" and module != topic:
            continue
        pool = [q for q in bank if q["topic"] == topic]
        shuffle(pool)
        questions.extend(pool[:4 if module == "all" else 6])
    shuffle(questions)
    return questions


def limit_auth_attempts(action: str) -> Any | None:
    # Uses the direct remote address only. Do not trust arbitrary forwarded headers.
    bucket = __import__("hashlib").sha256(f"{request.remote_addr}|{action}".encode()).hexdigest()
    now = int(time.time())
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO auth_limits(bucket, failures, window_start) VALUES (%s, 0, %s) ON DUPLICATE KEY UPDATE bucket=bucket", (bucket, now))
        cur.execute("SELECT failures, window_start FROM auth_limits WHERE bucket=%s FOR UPDATE", (bucket,))
        row = cur.fetchone()
        if now - int(row["window_start"]) >= 900:
            cur.execute("UPDATE auth_limits SET failures=0, window_start=%s WHERE bucket=%s", (now, bucket))
            row["failures"] = 0
        if int(row["failures"]) >= 20:
            conn.commit()
            return error("Too many account requests. Please try again in 15 minutes.", 429)
        cur.execute("UPDATE auth_limits SET failures=failures+1 WHERE bucket=%s", (bucket,))
        conn.commit()
    return None


@app.get("/")
def home():
    return send_from_directory(ROOT, "index.html")


@app.get("/api/auth.php")
def auth_status():
    return api({"csrf": csrf(), "loggedIn": "user_id" in session})


@app.post("/api/auth.php")
def auth_action():
    body, problem = read_body()
    if problem:
        return problem
    action = body.get("action")
    if action == "logout":
        session.clear()
        csrf()
        return api({"ok": True, "csrf": csrf()})
    if action not in {"login", "register"}:
        return error("Unknown action.")
    email = str(body.get("email", "")).strip().lower()
    password = body.get("password")
    if "@" not in email or len(email) > 190 or not isinstance(password, str) or not 8 <= len(password) <= 72:
        return error("Enter a valid email and a password of 8–72 characters.")
    limited = limit_auth_attempts(action)
    if limited:
        return limited
    with db() as conn, conn.cursor() as cur:
        if action == "register":
            name = str(body.get("name", "")).strip()
            if not 2 <= len(name) <= 80:
                return error("Use a name between 2 and 80 characters.")
            try:
                cur.execute("INSERT INTO users(name, email, password_hash) VALUES (%s, %s, %s)", (name, email, generate_password_hash(password)))
                user_id = cur.lastrowid
                conn.commit()
            except pymysql.err.IntegrityError:
                conn.rollback()
                return error("This email is already registered. Please log in.", 409)
        else:
            cur.execute("SELECT id, password_hash FROM users WHERE email=%s", (email,))
            row = cur.fetchone()
            if not row or not check_password_hash(row["password_hash"], password):
                return error("Email or password is incorrect.", 401)
            user_id = row["id"]
    session.clear()
    session["user_id"] = user_id
    csrf()
    return api({"ok": True, "csrf": csrf()})


@app.get("/api/learning.php")
def learning_get():
    user, problem = get_user()
    if problem:
        return problem
    attempt_id = request.args.get("id")
    with db() as conn, conn.cursor() as cur:
        if attempt_id:
            cur.execute("SELECT * FROM attempts WHERE id=%s AND user_id=%s AND status='completed'", (attempt_id, user["id"]))
            row = cur.fetchone()
            return api(complete_result(row)) if row else error("Attempt not found.", 404)
        cur.execute("SELECT lesson_id FROM progress WHERE user_id=%s", (user["id"],))
        completed = [r["lesson_id"] for r in cur.fetchall()]
        cur.execute("SELECT id, module_id, score, total, completed_at FROM attempts WHERE user_id=%s AND status='completed' ORDER BY completed_at DESC", (user["id"],))
        attempts = [{"id": r["id"], "moduleId": r["module_id"], "score": r["score"], "total": r["total"], "completedAt": iso(r["completed_at"])} for r in cur.fetchall()]
    return api({"name": user["name"], "email": user["email"], "csrf": csrf(), "completed": completed, "attempts": attempts})


@app.post("/api/learning.php")
def learning_post():
    user, problem = get_user()
    if problem:
        return problem
    body, problem = read_body()
    if problem:
        return problem
    action = body.get("action")
    if action == "complete":
        lesson_id = body.get("lessonId")
        if lesson_id not in LESSONS:
            return error("Unknown lesson.")
        with db() as conn, conn.cursor() as cur:
            cur.execute("INSERT IGNORE INTO progress(user_id, lesson_id) VALUES (%s, %s)", (user["id"], lesson_id))
            conn.commit()
        return api({"ok": True})
    if action == "start":
        module = body.get("moduleId")
        if module not in MODULES:
            return error("Unknown quiz.")
        questions = load_questions(module)
        attempt_id = secrets.token_hex(16)
        with db() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO attempts(id, user_id, module_id, questions, total) VALUES (%s, %s, %s, %s, %s)", (attempt_id, user["id"], module, json.dumps(questions, ensure_ascii=False), len(questions)))
            conn.commit()
        safe_questions = [{k: v for k, v in q.items() if k not in {"answer", "explanation"}} for q in questions]
        return api({"id": attempt_id, "moduleId": module, "questions": safe_questions})
    if action == "submit":
        attempt_id, answers = body.get("id"), body.get("answers")
        if not isinstance(attempt_id, str) or not isinstance(answers, dict):
            return error("Invalid submission.")
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM attempts WHERE id=%s AND user_id=%s FOR UPDATE", (attempt_id, user["id"]))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return error("Attempt not found.", 404)
            if row["status"] == "completed":
                conn.commit()
                return api(complete_result(row))
            details: list[dict[str, Any]] = []
            saved_answers: dict[str, str] = {}
            score = 0
            for question in json.loads(row["questions"]):
                given = answers.get(question["id"])
                if not isinstance(given, str) or not given.strip() or len(given) > 200:
                    conn.rollback()
                    return error("Answer every question before submitting.")
                given = given.strip()
                saved_answers[question["id"]] = given
                correct = normalize(given, bool(question.get("numeric"))) == normalize(question["answer"], bool(question.get("numeric")))
                details.append({**question, "given": given, "correct": correct})
                score += int(correct)
            result = {"score": score, "total": len(details), "details": details}
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            cur.execute("UPDATE attempts SET status='completed', answers=%s, result=%s, score=%s, completed_at=%s WHERE id=%s AND user_id=%s", (json.dumps(saved_answers, ensure_ascii=False), json.dumps(result, ensure_ascii=False), score, now, row["id"], user["id"]))
            conn.commit()
        result.update({"id": row["id"], "moduleId": row["module_id"], "completedAt": iso(now)})
        return api(result)
    return error("Unknown action.")


@app.errorhandler(Exception)
def server_error(exc: Exception):
    app.logger.exception("LogicLab server error", exc_info=exc)
    return api({"error": "Server error. Check MySQL, your config.py file, and the Flask terminal."}, 503)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
