"""Fill the app with demo data:  python seed.py      (Owner: Rafi)
Login afterwards with  demo / demo1234
Last month ends with money left over, so you can try the carry / savings decision.
"""
from datetime import date

from werkzeug.security import generate_password_hash

import services as svc
from app import create_app
import db as database

app = create_app()
with app.app_context():
    db = database.get_db()
    if db.execute("SELECT 1 FROM users WHERE username = 'demo'").fetchone():
        raise SystemExit("Demo user already exists. Delete instance/takatrack.sqlite to start fresh.")

    today = date.today()
    py, pm = svc.prev_month(today.year, today.month)
    with db:
        uid = db.execute("INSERT INTO users (username, password_hash, monthly_budget) VALUES (?,?,?)",
                         ("demo", generate_password_hash("demo1234"), 20000)).lastrowid
        cats = {}
        for name, limit in [("Food", 8000), ("Transport", 3000), ("Bills", 6000), ("Fun", None)]:
            cats[name] = db.execute(
                "INSERT INTO categories (user_id, name, monthly_limit, limit_asked) VALUES (?,?,?,1)",
                (uid, name, limit)).lastrowid
        for y, m in [(py, pm), (today.year, today.month)]:
            db.execute("INSERT INTO monthly_budgets (user_id, year, month, base_amount) VALUES (?,?,?,20000)",
                       (uid, y, m))
        rows = [  # (year, month, day, category, title, amount)
            (py, pm, 3, "Bills", "Electricity bill", 2500), (py, pm, 8, "Food", "Groceries", 4200),
            (py, pm, 15, "Transport", "Rickshaw and bus", 1800), (py, pm, 21, "Fun", "Cinema", 900),
            (today.year, today.month, 2, "Bills", "Internet bill", 1200),
            (today.year, today.month, 3, "Food", "Groceries", 3500),
            (today.year, today.month, 5, "Transport", "CNG fare", 2400),
        ]
        for y, m, d, cat, title, amount in rows:
            db.execute("INSERT INTO expenses (user_id, category_id, title, amount, spent_on) VALUES (?,?,?,?,?)",
                       (uid, cats[cat], title, amount, f"{y}-{m:02d}-{d:02d}"))
    print("Demo data created. Login: demo / demo1234")
