"""Shared helpers: money format, month dates, and the spending SQL.

Owner: Samia. Everybody imports from here, so change it carefully.
"""
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def format_taka(amount):
    """1234567 -> ৳12,34,567 (Bangladeshi digit grouping)."""
    n = int(amount or 0)
    sign = "-" if n < 0 else ""
    digits = str(abs(n))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        digits = ",".join(parts + [tail])
    return f"{sign}৳{digits}"


def month_label(year, month):
    return f"{MONTH_NAMES[month - 1]} {year}"


def next_month(year, month):
    return (year + 1, 1) if month == 12 else (year, month + 1)


def prev_month(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def month_bounds(year, month):
    """Return (first day of month, first day of next month) as text."""
    ny, nm = next_month(year, month)
    return f"{year:04d}-{month:02d}-01", f"{ny:04d}-{nm:02d}-01"


def month_spent(db, user_id, year, month, category_id=None):
    start, end = month_bounds(year, month)
    sql = ("SELECT COALESCE(SUM(amount), 0) FROM expenses "
           "WHERE user_id = ? AND spent_on >= ? AND spent_on < ?")
    args = [user_id, start, end]
    if category_id is not None:
        sql += " AND category_id = ?"
        args.append(category_id)
    return db.execute(sql, args).fetchone()[0]
