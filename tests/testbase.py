"""Shared test setup (Samia). Every test file imports TakaTrackTestCase from here."""
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

TODAY = date(2026, 11, 18)   # fixed "today" so the tests never depend on the real date


class TakaTrackTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path,
                               "TODAY": TODAY, "SECRET_KEY": "test"})
        self.client = self.app.test_client()
        self.register_and_login(self.client, "rafi")

    def tearDown(self):
        os.remove(self.db_path)

    # ---- helpers
    def post(self, client, url, data=None, follow=False):
        with client.session_transaction() as s:
            s["_csrf"] = "tok"
        payload = dict(data or {}, _csrf="tok")
        return client.post(url, data=payload, follow_redirects=follow)

    def register_and_login(self, client, name):
        self.post(client, "/register", {"username": name, "password": "secret123"})
        self.post(client, "/login", {"username": name, "password": "secret123"})

    def sql(self, query, args=()):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        rows = con.execute(query, args).fetchall()
        con.commit()
        con.close()
        return rows

    def user_id(self, name="rafi"):
        return self.sql("SELECT id FROM users WHERE username = ?", (name,))[0]["id"]

    def add_category(self, name, limit=None):
        self.sql("INSERT INTO categories (user_id, name, monthly_limit, limit_asked) VALUES (?,?,?,1)",
                 (self.user_id(), name, limit))
        return self.sql("SELECT id FROM categories WHERE name = ?", (name,))[0]["id"]

    def add_expense_row(self, category_id, amount, day, user="rafi"):
        self.sql("INSERT INTO expenses (user_id, category_id, title, amount, spent_on) VALUES (?,?,?,?,?)",
                 (self.user_id(user), category_id, "test", amount, day))

    def expense_count(self):
        return self.sql("SELECT COUNT(*) AS n FROM expenses")[0]["n"]

    def october_with_leftover(self, spent=7000):
        """October budget 10,000 with `spent` taka spent -> leftover = 10,000 - spent."""
        self.sql("INSERT INTO monthly_budgets (user_id, year, month, base_amount) VALUES (?,?,?,?)",
                 (self.user_id(), 2026, 10, 10000))
        cat = self.add_category("Food")
        self.add_expense_row(cat, spent, "2026-10-15")
