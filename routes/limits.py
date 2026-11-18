"""Owner: Hrishika. The Spending limits page."""
import re

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

import db as database
import services as svc
from helpers import get_today, login_required, parse_whole_number

bp = Blueprint("limits", __name__)


@bp.route("/limits", methods=["GET", "POST"])
@login_required
def limits():
    db, today, uid = database.get_db(), get_today(), g.user["id"]
    if request.method == "POST":
        raw = request.form.get("limit", "").strip()
        limit = parse_whole_number(raw, minimum=1) if raw else None
        if raw and limit is None:
            flash("The limit must be a whole number of taka, 1 or more.", "error")
            return redirect(url_for("limits.limits"))
        new_name = re.sub(r"\s+", " ", request.form.get("new_name", "").strip())
        with db:
            if new_name:
                if svc.find_category(db, uid, new_name):
                    flash("That category already exists.", "error")
                else:
                    db.execute("INSERT INTO categories (user_id, name, monthly_limit, "
                               "limit_asked) VALUES (?, ?, ?, 1)", (uid, new_name, limit))
                    flash(f"Category {new_name} added.", "success")
            else:
                db.execute("UPDATE categories SET monthly_limit = ?, limit_asked = 1 "
                           "WHERE id = ? AND user_id = ?",
                           (limit, request.form.get("category_id"), uid))
                flash("Limit saved." if limit else "Limit removed.", "success")
        return redirect(url_for("limits.limits"))
    return render_template("limits/limits.html", categories=svc.category_rows(
        db, uid, today.year, today.month), label=svc.month_label(today.year, today.month))
