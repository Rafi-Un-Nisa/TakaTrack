"""Owner: Samia. Dashboard page and the Excel report (Pandas)."""
import io

import pandas as pd
from flask import Blueprint, g, render_template, request, send_file

import db as database
import services as svc
from helpers import get_today, login_required, parse_month

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def dashboard():
    db, today, uid = database.get_db(), get_today(), g.user["id"]
    y, m = parse_month(request.args.get("month"))
    row = svc.budget_row_for(db, uid, y, m, today)
    start, end = svc.month_bounds(y, m)
    recent = db.execute(
        """SELECT e.*, c.name AS category FROM expenses e
           JOIN categories c ON c.id = e.category_id
           WHERE e.user_id = ? AND e.spent_on >= ? AND e.spent_on < ?
           ORDER BY e.spent_on DESC, e.id DESC LIMIT 8""",
        (uid, start, end)).fetchall()
    py, pm = svc.prev_month(y, m)
    ny, nm = svc.next_month(y, m)
    return render_template(
        "dashboard/dashboard.html",
        label=svc.month_label(y, m),
        summary=svc.budget_summary(db, uid, y, m, row),
        categories=svc.category_rows(db, uid, y, m),
        recent=recent,
        pending=svc.pending_rollover(db, uid, today),
        savings=svc.savings_total(db, uid),
        prev_key=f"{py}-{pm:02d}", next_key=f"{ny}-{nm:02d}",
        month_key=f"{y}-{m:02d}")


@bp.route("/report.xlsx")
@login_required
def report():
    """Excel report made with Pandas (3 sheets)."""
    db, today, uid = database.get_db(), get_today(), g.user["id"]
    y, m = parse_month(request.args.get("month"))
    start, end = svc.month_bounds(y, m)
    expenses_df = pd.read_sql_query(
        """SELECT e.spent_on AS Date, c.name AS Category, e.title AS Item,
                  e.amount AS Amount, e.note AS Note
           FROM expenses e JOIN categories c ON c.id = e.category_id
           WHERE e.user_id = ? AND e.spent_on >= ? AND e.spent_on < ?
           ORDER BY e.spent_on""", db, params=(uid, start, end))
    cats = svc.category_rows(db, uid, y, m)
    category_df = pd.DataFrame(
        [{"Category": c["name"], "Limit": c["limit"], "Spent": c["spent"],
          "Left": c["left"]} for c in cats],
        columns=["Category", "Limit", "Spent", "Left"])
    s = svc.budget_summary(db, uid, y, m, svc.get_month_budget(db, uid, y, m))
    summary_df = pd.DataFrame({
        "Item": ["Base budget", "Carried over", "Total budget", "Spent", "Remaining"],
        "Taka": [s.get("base", 0), s.get("carried", 0), s.get("total", 0),
                 s["spent"], s.get("remaining", 0)]})
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        category_df.to_excel(writer, sheet_name="By category", index=False)
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"takatrack-{y}-{m:02d}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
