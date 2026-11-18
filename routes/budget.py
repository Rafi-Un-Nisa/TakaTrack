"""Owner: Rafi. Recurring budget, month-end rollover, savings."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

import db as database
import services as svc
from helpers import get_today, login_required, parse_whole_number

bp = Blueprint("budget", __name__)


@bp.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    db, today = database.get_db(), get_today()
    if request.method == "POST":
        amount = parse_whole_number(request.form.get("amount", ""), minimum=0)
        if amount is None:
            flash("Enter a whole number of taka (0 or more).", "error")
        else:
            svc.set_recurring_budget(db, g.user["id"], amount, today)
            flash("Monthly budget saved. It repeats every month automatically.", "success")
            return redirect(url_for("dashboard.dashboard"))
    current = db.execute("SELECT monthly_budget FROM users WHERE id = ?",
                         (g.user["id"],)).fetchone()[0]
    return render_template("budget/budget.html", current=current)


@bp.route("/rollover/<int:year>/<int:month>", methods=["GET", "POST"])
@login_required
def rollover(year, month):
    db, today, uid = database.get_db(), get_today(), g.user["id"]
    try:
        info = svc.rollover_preview(db, uid, year, month, today)
    except svc.RolloverError as error:
        flash(str(error), "error")
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        carry = parse_whole_number(request.form.get("carry", "0") or "0")
        save = parse_whole_number(request.form.get("save", "0") or "0")
        if carry is None or save is None:
            flash("Enter whole numbers (0 or more).", "error")
        else:
            try:
                svc.close_month(db, uid, year, month, carry, save, today)
            except svc.RolloverError as error:
                flash(str(error), "error")
            else:
                flash(f"Done: {svc.format_taka(carry)} carried to {info['next_label']}, "
                      f"{svc.format_taka(save)} moved to savings.", "success")
                return redirect(url_for("dashboard.dashboard"))
    return render_template("budget/rollover.html", info=info)


@bp.route("/savings")
@login_required
def savings():
    db, uid = database.get_db(), g.user["id"]
    history = db.execute(
        "SELECT year, month, leftover, carried, saved FROM rollovers "
        "WHERE user_id = ? ORDER BY year DESC, month DESC", (uid,)).fetchall()
    rows = [{"label": svc.month_label(r["year"], r["month"]), **dict(r)} for r in history]
    return render_template("budget/savings.html", total=svc.savings_total(db, uid), rows=rows)
