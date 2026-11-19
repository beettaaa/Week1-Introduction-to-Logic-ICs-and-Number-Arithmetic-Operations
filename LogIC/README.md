# LogicLab - Flask + MySQL

This ZIP is the Flask version of the CPET12L reviewer. It has account registration and login. Every learner's completed lessons, quiz answers, scores, and attempt date are saved in MySQL under that account.

## Run it on Windows with XAMPP

1. Extract `LogicLab-Flask-MySQL.zip` anywhere convenient, such as your Documents folder. It does **not** need to go inside `htdocs` because Flask runs the website itself.
2. Open XAMPP Control Panel and start **MySQL**. Apache is not required for this Flask version.
3. Open `http://localhost/phpmyadmin` in your browser. Select **Import**, choose `database/logiclab.sql`, and click **Go**. This creates the `logiclab` database and the `users`, `attempts`, `progress`, and `auth_limits` tables.
4. Open Command Prompt inside the extracted `LogicLab-Flask-MySQL` folder. Run these commands:

   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

   If `py` is not recognized, install Python 3.10 or newer from python.org and select **Add Python to PATH** during installation. You can use `python` instead of `py` after that.

5. Open **http://127.0.0.1:5000**. Select **Log in / Register**, make an account, then complete a quiz. Your answers and score appear under **My progress**.

Keep the Command Prompt window open while the website is running. To stop Flask, press `Ctrl + C` in that window.

## MySQL connection settings

The defaults in `config.py` work for many local XAMPP installations:

| Setting | Default |
| --- | --- |
| Host | `127.0.0.1` |
| Port | `3306` |
| Database | `logiclab` |
| User | `root` |
| Password | empty |

If your XAMPP MySQL account has a password, set `DB_PASSWORD` in `config.py`. If you renamed the database, update `DB_NAME` too.

## Files included

| File or folder | Purpose |
| --- | --- |
| `app.py` | Flask server: routes, registration/login, quiz grading, saved results |
| `config.py` | MySQL connection and session configuration |
| `requirements.txt` | Flask and PyMySQL packages to install |
| `database/logiclab.sql` | Import this file in phpMyAdmin first |
| `api/private/questions.json` | Server-side quiz question bank |
| `assets/` | Ready-to-run JavaScript, CSS, and favicon |
| `src/` | Editable React/TypeScript source of the reviewer |
| `index.html` | Main page loaded by Flask |

The browser JavaScript sends account and learning requests to Flask paths called `/api/auth.php` and `/api/learning.php`. The `.php` endings are retained only so the prepared frontend can work without changes. They are handled by Flask, not PHP; no PHP installation or Apache server is required.

## How scores are saved

`users` stores each registered account. `attempts` stores the account ID, question set, submitted answers, detailed feedback, score, total questions, and completion time. `progress` stores the completed lesson IDs for that account. The server checks the signed-in account before reading or writing any attempt, so one learner cannot open another learner's history.

Passwords are stored as hashes, not readable text. The Flask API grades quizzes on the server; a browser cannot send its own score. Login and registration are rate-limited, and POST requests use a session CSRF token.

## Optional source changes

The ready-to-run JavaScript is already in `assets/app.js`; you do not need Node.js just to run the website. To change lessons, layout, or activities, edit `src/` and rebuild with Node.js:

```bat
npm install
npm run check
npm run build
```

Useful source files:

- `src/lib/course.ts` - lessons and references
- `src/App.tsx` - navigation, quiz display, progress screen
- `src/Account.tsx` - register/login screen
- `src/Workbench.tsx` - calculators and IC explorer
- `app.py` - quiz saving, account logic, and MySQL queries

## Common problems

- **`Access denied for user root`:** add your MySQL password in `config.py`.
- **`Unknown database logiclab`:** import `database/logiclab.sql` in phpMyAdmin.
- **`ModuleNotFoundError: flask`:** activate `.venv`, then run `pip install -r requirements.txt`.
- **Website will not open:** make sure `python app.py` is still running, then use the exact URL `http://127.0.0.1:5000`.
- **Session expired:** refresh the browser and log in again.
- **MySQL service will not start in XAMPP:** another program may already be using port 3306. Check the XAMPP MySQL log or change the port in both XAMPP and `config.py`.

## Before hosting outside your computer

Set `FLASK_SECRET_KEY` to a long random secret, set `FLASK_HTTPS=true`, use HTTPS, and create a dedicated MySQL user instead of `root`. This package is designed for local development and class demonstration. It does not include email verification, password reset, teacher accounts, or public deployment configuration.
