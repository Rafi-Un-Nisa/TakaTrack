"""Small helpers shared by all routes (login check, form parsing, today's date).
SHARED file (integrator: Rafi).

Shared file: change it only through a Pull Request that everybody reviews.
"""
import secrets
from datetime import date
from functools import wraps

from flask import current_app, g, redirect, session, url_for


def get_today():
    """Today's date. Tests can set app.config["TODAY"] to freeze the date."""
    return current_app.config.get("TODAY") or date.today()


def csrf_token():
    """Secret token that every POST form must send back (protects against CSRF)."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def parse_whole_number(text, minimum=0):
    """'500' -> 500. Returns None if it is not a whole number or is below `minimum`."""
    try:
        value = int(str(text).strip())
    except ValueError:
        return None
    return value if value >= minimum else None


def parse_month(text):
    """'2026-11' -> (2026, 11). Falls back to the current month."""
    today = get_today()
    try:
        y, m = map(int, (text or "").split("-"))
        if 1 <= m <= 12 and 2000 <= y <= 2100:
            return y, m
    except ValueError:
        pass
    return today.year, today.month
