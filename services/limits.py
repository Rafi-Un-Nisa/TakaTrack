"""Category spending limits and caution messages.

Owner: Hrishika.
"""
from .budget import budget_row_for
from .common import format_taka, month_bounds, month_label, month_spent


def category_rows(db, user_id, year, month):
    start, end = month_bounds(year, month)
    rows = db.execute(
        """SELECT c.id, c.name, c.monthly_limit AS limit_amount,
                  COALESCE(SUM(e.amount), 0) AS spent
           FROM categories c
           LEFT JOIN expenses e ON e.category_id = c.id
                AND e.spent_on >= ? AND e.spent_on < ?
           WHERE c.user_id = ?
           GROUP BY c.id ORDER BY c.name""", (start, end, user_id)).fetchall()
    result = []
    for r in rows:
        limit, spent = r["limit_amount"], r["spent"]
        if limit is None:
            status, percent = "none", 0
        else:
            percent = round(spent * 100 / limit)
            status = "over" if spent > limit else ("near" if spent >= 0.8 * limit else "ok")
        result.append({"id": r["id"], "name": r["name"], "limit": limit,
                       "spent": spent, "percent": percent, "bar": min(percent, 100),
                       "status": status,
                       "left": None if limit is None else limit - spent})
    return result


def find_category(db, user_id, name):
    return db.execute("SELECT * FROM categories WHERE user_id = ? AND name = ?",
                      (user_id, name)).fetchone()   # NOCASE: "food" finds "Food"


def expense_warnings(db, user_id, today, spent_on, amount, category_name,
                     category_id, limit):
    """Caution messages for a NEW expense (before it is saved)."""
    warnings = []
    y, m = spent_on.year, spent_on.month
    if limit is not None:
        already = month_spent(db, user_id, y, m, category_id) if category_id else 0
        total_after = already + amount
        if total_after > limit:
            warnings.append({
                "kind": "category",
                "message": (f"Caution: {category_name} would reach {format_taka(total_after)} "
                            f"of its {format_taka(limit)} monthly limit "
                            f"(over by {format_taka(total_after - limit)})."),
            })
    row = budget_row_for(db, user_id, y, m, today)
    if row:
        total = row["base_amount"] + row["carried_over"]
        after = month_spent(db, user_id, y, m) + amount
        if after > total:
            warnings.append({
                "kind": "month",
                "message": (f"Caution: this goes over your {month_label(y, m)} budget of "
                            f"{format_taka(total)} (over by {format_taka(after - total)})."),
            })
    return warnings
