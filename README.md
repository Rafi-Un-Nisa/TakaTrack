# TakaTrack - Personal Budget Tracker (৳)

A web app that helps you plan a monthly budget in Taka, track expenses by category,
get a caution before you overspend, and decide what to do with leftover money at month-end.

**Stack:** Python 3 - Flask - SQLite (plain SQL) - HTML / CSS / a little JavaScript - Pandas (Excel report) - Git

## Run it (3 commands)

    pip install -r requirements.txt
    python seed.py                 # optional demo data, login: demo / demo1234
    python -m flask --app app run  # open http://127.0.0.1:5000

Run the tests: `python -m unittest discover -s tests -v`

## The two main features

### 1. Recurring budget + month-end rollover
- **Budget page**: set a monthly budget once. It repeats every month automatically
  (the current month is created the first time you open the app that month).
- When a month ends with money left over, the dashboard shows a banner.
  **Decide now** lets you enter how much to **carry to next month** and how much to **move to savings**.
  Whatever you do not assign is released. A month can only be decided once.
- Carried money is added to next month's budget (`monthly_budgets.carried_over`).
  Savings are recorded in `rollovers.saved` and summed on the Savings page.

### 2. Category limits and caution
- Type any category when adding an expense. If it is **new** (or has no limit and was never asked),
  the app asks for a **monthly limit** for it first. You can skip once.
  Limits can also be set any time on the **Spending limits** page.
- If an expense would push a category over its limit, or the whole month over the budget,
  you see a **caution** (live while typing, and again before saving) and must press **Add anyway**.

Other pages: dashboard with progress bars, expense list with delete, Excel export (Pandas, 3 sheets).

## Where things are (read in this order)

| File / folder | What it does |
|---|---|
| `schema.sql` | The 6 database tables. Start here: users, categories, expenses, monthly_budgets, rollovers |
| `services/` | All money rules in plain Python + SQL: `common.py` (dates, totals), `budget.py` (rollover, savings), `limits.py` (limits, cautions) |
| `routes/` | The web pages, one file per feature: `auth`, `budget`, `expenses`, `limits`, `dashboard` |
| `app.py`, `helpers.py` | Wiring (app factory, login check, form parsing). Small shared files |
| `db.py` | Opens one SQLite connection per request |
| `templates/` | The pages (Jinja2 = HTML with placeholders like `{{ amount|taka }}`), one folder per feature + `base.html` |
| `static/style.css`, `static/app.js` | Styling, and the live caution that calls `/api/check` |
| `tests/` | 25 automated tests: `test_budget.py`, `test_limits.py`, `test_security_report.py` |
| `seed.py` | Demo data |
| `TEAM_WORK.md` | Who owns which files (Rafi, Hrishika, Samia), what to say about each part, and the Git workflow |

## Short explanation
"TakaTrack is a budget tracker for Bangladeshi users. You set a monthly budget that repeats automatically.
Every expense has a category with an optional monthly limit; if I add a new category it asks for a limit,
and if an expense goes over the limit it shows a caution. At the end of the month, leftover money can be
carried to the next month or moved to savings. It is built with Flask and SQL, the data is stored in
SQLite, and I wrote tests for the budget rules. I can also export a monthly Excel report using Pandas."

## Basic questions related to this
- **Why SQLite?** No setup, one file. The SQL is standard, so moving to PostgreSQL/MySQL means changing the connection code and a few column types.
- **Why store money as whole taka (INTEGER)?** Decimals/floats can create rounding errors in money.
- **How is a user's data kept private?** Every query has `WHERE user_id = ?` using the logged-in user.
- **How are passwords stored?** Only as a hash (`generate_password_hash`), never as plain text.
- **What is CSRF?** A trick where another site makes your browser send a form. Every form has a secret token that the server checks.
- **How does the month-end decision avoid double counting?** `rollovers` has `UNIQUE(user_id, year, month)` and the insert and the budget update happen in one transaction.
- **What is a JOIN?** Combining tables, e.g. `expenses JOIN categories` to show the category name next to each expense.
- **What would you improve?** Edit expenses, income tracking, charts, PostgreSQL + deployment, a password reset flow.

## Honest note
Read `services/` and `schema.sql` until you can explain each function.
