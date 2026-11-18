"""TakaTrack - application factory.   SHARED file (integrator: Rafi); change via Pull Request.

This file only wires things together. The real work is in:
  routes/    - one file per feature (the web pages)
  services/  - the money rules (plain Python + SQL)
  schema.sql - the database tables
"""
import os

from flask import Flask, abort, g, request, session

import db as database
import services as svc
from helpers import csrf_token
from routes import auth, budget, dashboard, expenses, limits


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "takatrack.sqlite"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    database.init_app(app)

    app.jinja_env.filters["taka"] = svc.format_taka
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def load_user_and_check_csrf():
        if request.method == "POST":
            if not session.get("_csrf") or session["_csrf"] != request.form.get("_csrf"):
                abort(400, "Bad form token. Please go back and try again.")
        g.user = None
        if session.get("user_id"):
            g.user = database.get_db().execute(
                "SELECT id, username, monthly_budget FROM users WHERE id = ?",
                (session["user_id"],)).fetchone()

    for module in (auth, budget, dashboard, expenses, limits):
        app.register_blueprint(module.bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
