# NumaLogi

A digital-logic learning space with logic circuit IC references, number-system conversion, and arithmetic. Built with **Python (Flask)**, **MariaDB**, **HTML**, **CSS**, and **JavaScript**.

## 1. Requirements

- Python 3.10 or newer
- MariaDB Server running locally (or a reachable MariaDB instance)
- A terminal in this project folder

## 2. Create the database

1. Open a MariaDB administrator terminal.
2. Run the included `schema.sql` script. For example:

   ```bash
   mariadb -u root -p < schema.sql
   ```

3. The script creates the `bitgate` database, the `bitgate_user` account, and the `users` table.
4. **Change the example database password in `schema.sql` before running it.** Use the same password for `DB_PASSWORD` below.

If your MariaDB account is not connecting from `localhost`, update the SQL user host and the connection settings to match your setup.

## 3. Install Python dependencies

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Then install packages:

```bash
python -m pip install -r requirements.txt
```

## 4. Configure and run

Set environment variables before starting the app. At minimum, set a strong `SECRET_KEY`, the database password, and a private professor access code.

Windows PowerShell:

```powershell
$env:SECRET_KEY="replace-with-a-long-random-secret"
$env:DB_PASSWORD="your-database-password"
$env:PROFESSOR_CODE="your-private-professor-code"
python app.py
```

macOS/Linux:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
export DB_PASSWORD="your-database-password"
export PROFESSOR_CODE="your-private-professor-code"
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The app checks the database connection and creates the `users` table if it is missing.

Optional database settings: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME`. Optional web port: `PORT`.

## Features

- Student and professor registration/login, password hashing, CSRF-protected forms, and session-based access.
- MariaDB-backed account storage.
- Reference tables for common 74xx logic ICs and logic-gate truth tables.
- Live binary, octal, decimal, and hexadecimal conversion.
- Addition, subtraction, multiplication, and integer division with quotient and remainder.
- Responsive emerald interface with a dark/light theme toggle.

## Project structure

- `app.py` — Flask routes, authentication, database access, and session security
- `schema.sql` — MariaDB database, user, and table setup
- `templates/` — landing, authentication, and learning dashboard pages
- `static/css/style.css` — responsive interface and themes
- `static/js/` — theme control and number-system tools

## Important notes

- The included database credentials and professor code are examples. Replace them before deployment.
- The default server binds to `127.0.0.1` and runs with Flask debug mode disabled. Use a production WSGI server for deployment.
- Each email address can register once. Student and professor accounts use the same email uniqueness rule.
