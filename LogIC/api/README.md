# NumaLogi

Intro to logic circuit ICs, number system conversion and arithmetic (Flask + MariaDB).

## Setup
1. Install MariaDB and create the database: run `schema.sql` (change the password in it first).
2. `pip install -r requirements.txt`
3. Edit the DB_* settings and PROFESSOR_CODE at the top of `app.py` (or use environment variables).
4. `python app.py` then open http://127.0.0.1:5000

## Structure
- app.py - routes, login/sign up, MariaDB access
- templates/ - base, landing, auth (login/sign up, student/professor), dashboard
- static/css/style.css - emerald theme, dark/light
- static/js/ - theme toggle, converter and arithmetic
- static/img/ - put tup.png and acts.png here
- schema.sql - database setup
