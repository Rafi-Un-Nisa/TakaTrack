"""Owner: Hrishika. Add / list / delete expenses and the live caution API."""
import re
from datetime import datetime

from flask import (Blueprint, abort, flash, g, jsonify, redirect, render_template,
                   request, url_for)

import db as database
import services as svc
from helpers import get_today, login_required, parse_month, parse_whole_number

bp = Blueprint("expenses", __name__)


def render_add(form, categories, **extra):
    ctx = {"need_limit": False, "warnings": [], "skip": False}
    ctx.update(extra)
    return render_template("expenses/expense_form.html", form=form,
                           categories=categories, **ctx)


@bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    db, today, uid = database.get_db(), get_today(), g.user["id"]
    categories = db.execute("SELECT name FROM categories WHERE user_id = ? ORDER BY name",
                            (uid,)).fetchall()
    form = {"title": "", "amount": "", "category": "",
            "spent_on": today.isoformat(), "note": "", "limit": ""}
    if request.method == "GET":
        return render_add(form, categories)

    for key in form:
        form[key] = request.form.get(key, "").strip()
    form["category"] = re.sub(r"\s+", " ", form["category"])
    skip = request.form.get("skip_limit") == "1"
    confirm = request.form.get("confirm") == "1"

    # 1) basic checks
    errors = []
    amount = parse_whole_number(form["amount"], minimum=1)
    if not form["title"]:
        errors.append("Please enter what you spent on.")
    if amount is None:
        errors.append("Amount must be a whole number of taka, 1 or more.")
    if not form["category"]:
        errors.append("Please choose or type a category.")
    try:
        spent_on = datetime.strptime(form["spent_on"], "%Y-%m-%d").date()
    except ValueError:
        spent_on = None
        errors.append("Please enter a valid date.")
    limit_value = None
    if form["limit"]:
        limit_value = parse_whole_number(form["limit"], minimum=1)
        if limit_value is None:
            errors.append("The limit must be a whole number of taka, 1 or more.")
    if errors:
        for e in errors:
            flash(e, "error")
        return render_add(form, categories, skip=skip)

    # 2) FEATURE: new category (or no limit yet) -> ask for a limit
    category = svc.find_category(db, uid, form["category"])
    existing_limit = category["monthly_limit"] if category else None
    never_asked = category is None or (existing_limit is None and not category["limit_asked"])
    if never_asked and limit_value is None and not skip:
        return render_add(form, categories, need_limit=True)

    # 3) FEATURE: caution when the limit / budget would be exceeded
    effective_limit = limit_value if limit_value is not None else existing_limit
    warnings = svc.expense_warnings(
        db, uid, today, spent_on, amount,
        category["name"] if category else form["category"],
        category["id"] if category else None, effective_limit)
    if warnings and not confirm:
        return render_add(form, categories, warnings=warnings, skip=skip)

    # 4) save everything in one transaction
    with db:
        if category is None:
            cur = db.execute(
                "INSERT INTO categories (user_id, name, monthly_limit, limit_asked) "
                "VALUES (?, ?, ?, 1)", (uid, form["category"], limit_value))
            category_id = cur.lastrowid
        else:
            category_id = category["id"]
            if limit_value is not None:
                db.execute("UPDATE categories SET monthly_limit = ?, limit_asked = 1 "
                           "WHERE id = ?", (limit_value, category_id))
            elif skip:
                db.execute("UPDATE categories SET limit_asked = 1 WHERE id = ?",
                           (category_id,))
        db.execute("INSERT INTO expenses (user_id, category_id, title, amount, spent_on, note) "
                   "VALUES (?, ?, ?, ?, ?, ?)",
                   (uid, category_id, form["title"], amount, spent_on.isoformat(), form["note"]))
    flash(f"Added {svc.format_taka(amount)} for {form['title']}.", "success")
    for w in warnings:
        flash(w["message"], "warning")
    return redirect(url_for("dashboard.dashboard", month=f"{spent_on.year}-{spent_on.month:02d}"))


@bp.route("/api/check")
@login_required
def api_check():
    """Used by app.js to show a caution while the user is still typing."""
    db, today, uid = database.get_db(), get_today(), g.user["id"]
    name = re.sub(r"\s+", " ", request.args.get("category", "").strip())
    amount = parse_whole_number(request.args.get("amount", ""), minimum=1)
    try:
        spent_on = datetime.strptime(request.args.get("date", ""), "%Y-%m-%d").date()
    except ValueError:
        spent_on = today
    if not name or amount is None:
        return jsonify(warnings=[], new_category=False)
    category = svc.find_category(db, uid, name)
    limit = category["monthly_limit"] if category else None
    warnings = svc.expense_warnings(db, uid, today, spent_on, amount,
                                    category["name"] if category else name,
                                    category["id"] if category else None, limit)
    return jsonify(warnings=[w["message"] for w in warnings],
                   new_category=category is None)


@bp.route("/expenses")
@login_required
def expenses():
    db, uid = database.get_db(), g.user["id"]
    y, m = parse_month(request.args.get("month"))
    start, end = svc.month_bounds(y, m)
    rows = db.execute(
        """SELECT e.*, c.name AS category FROM expenses e
           JOIN categories c ON c.id = e.category_id
           WHERE e.user_id = ? AND e.spent_on >= ? AND e.spent_on < ?
           ORDER BY e.spent_on DESC, e.id DESC""", (uid, start, end)).fetchall()
    return render_template("expenses/expenses.html", rows=rows, label=svc.month_label(y, m),
                           month_key=f"{y}-{m:02d}",
                           total=sum(r["amount"] for r in rows))


@bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    db = database.get_db()
    with db:
        cur = db.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?",
                         (expense_id, g.user["id"]))      # user_id check = privacy
    if cur.rowcount == 0:
        abort(404)
    flash("Expense deleted.", "success")
    return redirect(request.referrer or url_for("expenses.expenses"))
