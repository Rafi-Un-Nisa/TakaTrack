"""Recurring monthly budget, month-end rollover (carry / savings).

Owner: Rafi.
"""
from .common import format_taka, month_bounds, month_label, month_spent, next_month


class RolloverError(ValueError):
    """Raised when a month-end decision is not allowed."""


def get_month_budget(db, user_id, year, month):
    return db.execute(
        "SELECT * FROM monthly_budgets WHERE user_id = ? AND year = ? AND month = ?",
        (user_id, year, month)).fetchone()


def _ensure_month_budget(db, user_id, year, month, force=False):
    """Create the month's budget row from the user's recurring budget.
    Does NOT commit - the caller commits."""
    row = get_month_budget(db, user_id, year, month)
    if row:
        return row
    base = db.execute("SELECT monthly_budget FROM users WHERE id = ?",
                      (user_id,)).fetchone()[0]
    if base <= 0 and not force:
        return None
    db.execute("INSERT INTO monthly_budgets (user_id, year, month, base_amount) "
               "VALUES (?, ?, ?, ?)", (user_id, year, month, base))
    return get_month_budget(db, user_id, year, month)


def budget_row_for(db, user_id, year, month, today):
    """The CURRENT month is created automatically (recurring budget).
    Other months are only returned if they already exist."""
    if (year, month) == (today.year, today.month):
        row = _ensure_month_budget(db, user_id, year, month)
        db.commit()
        return row
    return get_month_budget(db, user_id, year, month)


def set_recurring_budget(db, user_id, amount, today):
    """Change the recurring budget; it also applies to the current month."""
    with db:
        db.execute("UPDATE users SET monthly_budget = ? WHERE id = ?", (amount, user_id))
        row = get_month_budget(db, user_id, today.year, today.month)
        if row:
            db.execute("UPDATE monthly_budgets SET base_amount = ? WHERE id = ?",
                       (amount, row["id"]))
        elif amount > 0:
            _ensure_month_budget(db, user_id, today.year, today.month)


def budget_summary(db, user_id, year, month, row):
    spent = month_spent(db, user_id, year, month)
    if row is None:
        return {"has_budget": False, "spent": spent}
    total = row["base_amount"] + row["carried_over"]
    remaining = total - spent
    percent = round(spent * 100 / total) if total > 0 else (100 if spent else 0)
    return {"has_budget": True, "base": row["base_amount"],
            "carried": row["carried_over"], "total": total, "spent": spent,
            "remaining": remaining, "percent": percent,
            "bar": min(percent, 100), "over": remaining < 0}


def rollover_preview(db, user_id, year, month, today):
    """Check a month can be closed and return its numbers."""
    if (year, month) >= (today.year, today.month):
        raise RolloverError("You can only decide about a month that has finished.")
    row = get_month_budget(db, user_id, year, month)
    if row is None:
        raise RolloverError("That month had no budget.")
    done = db.execute("SELECT 1 FROM rollovers WHERE user_id = ? AND year = ? AND month = ?",
                      (user_id, year, month)).fetchone()
    if done:
        raise RolloverError("You already decided about that month.")
    total = row["base_amount"] + row["carried_over"]
    spent = month_spent(db, user_id, year, month)
    leftover = total - spent
    if leftover <= 0:
        raise RolloverError("There is no money left over for that month.")
    ny, nm = next_month(year, month)
    return {"year": year, "month": month, "label": month_label(year, month),
            "total": total, "spent": spent, "leftover": leftover,
            "next_label": month_label(ny, nm)}


def pending_rollover(db, user_id, today):
    """The OLDEST finished month that still has leftover money and no decision."""
    rows = db.execute(
        """SELECT mb.year, mb.month FROM monthly_budgets mb
           WHERE mb.user_id = ? AND (mb.year * 100 + mb.month) < ?
             AND NOT EXISTS (SELECT 1 FROM rollovers r WHERE r.user_id = mb.user_id
                             AND r.year = mb.year AND r.month = mb.month)
           ORDER BY mb.year, mb.month""",
        (user_id, today.year * 100 + today.month)).fetchall()
    for r in rows:
        try:
            return rollover_preview(db, user_id, r["year"], r["month"], today)
        except RolloverError:
            continue                          # nothing left over -> nothing to decide
    return None


def close_month(db, user_id, year, month, carry, save, today):
    """Save the user's decision. Carried money is added to next month's budget."""
    info = rollover_preview(db, user_id, year, month, today)
    if carry < 0 or save < 0:
        raise RolloverError("Amounts cannot be negative.")
    if carry + save > info["leftover"]:
        raise RolloverError(f"You only have {format_taka(info['leftover'])} to share out.")
    ny, nm = next_month(year, month)
    with db:                                   # one transaction: all or nothing
        db.execute("INSERT INTO rollovers (user_id, year, month, leftover, carried, saved) "
                   "VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, year, month, info["leftover"], carry, save))
        if carry > 0:
            _ensure_month_budget(db, user_id, ny, nm, force=True)
            db.execute("UPDATE monthly_budgets SET carried_over = carried_over + ? "
                       "WHERE user_id = ? AND year = ? AND month = ?",
                       (carry, user_id, ny, nm))
    return info


def savings_total(db, user_id):
    return db.execute("SELECT COALESCE(SUM(saved), 0) FROM rollovers WHERE user_id = ?",
                      (user_id,)).fetchone()[0]
