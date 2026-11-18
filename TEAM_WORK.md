# TakaTrack - team plan: Rafi, Hrishika, Samia

The app is complete and tested (25 tests). The work is split into **three vertical slices**:
each person owns a feature from the database query to the page on screen, in **separate files**,
so Git merges do not collide. Only edit your own files. For a change in someone else's file,
ask them, or open a Pull Request.

Every file starts with an `Owner:` line, so you can always check who to ask.

## The three parts at a glance

| | **Rafi** | **Hrishika** | **Samia** |
|---|---|---|---|
| **Part** | Budget, Rollover & Savings + shared layout | Expenses & Spending Limits | Accounts, Dashboard, Reports & Database |
| **Feature** | Recurring monthly budget, month-end rollover (carry / savings), savings history | Add expense, ask for category limit, caution, live caution, expense list, limits page | Register / login / logout, dashboard, Excel report (Pandas), database schema |
| **routes/** | `budget.py` | `expenses.py`, `limits.py` | `auth.py`, `dashboard.py` |
| **services/** | `budget.py` | `limits.py` | `common.py` |
| **templates/** | `budget/` (3 pages), `base.html` | `expenses/` (2 pages), `limits/` | `auth/`, `dashboard/` |
| **Other files** | `static/style.css`, `seed.py` | `static/app.js` | `schema.sql`, `db.py` |
| **tests/** | `test_budget.py` | `test_limits.py` | `testbase.py`, `test_security_report.py` |
| **Size** | about 430 lines (hardest logic) | about 490 lines | about 500 lines |

**Why this split:** the rollover, the recurring budget and the savings all use the same two tables
(`monthly_budgets`, `rollovers`), so one person should own them together. The add-expense flow and the
limits page share one rule file, so they go together. Accounts, the database and the dashboard all
read from everything else, so they form the third part.

**Rafi** is also the integrator: creates the GitHub repo, owns the shared files (`app.py`, `helpers.py`,
`README.md`, `requirements.txt`) and checks Pull Requests before merging.

## What each person should know (and say in an interview)

### Rafi - Budget, Rollover & Savings
Read: `services/budget.py`, `routes/budget.py`, `templates/budget/`, `tests/test_budget.py`.
- "A month has one row in `monthly_budgets`: the base budget copied from my recurring budget, plus any amount carried over."
- "When a month ends with money left, I choose how much to carry and how much to save. The decision is saved in `rollovers`."
- "A month can only be decided once (`UNIQUE` constraint), and saving the decision and updating next month's budget happen in one transaction, so it is all-or-nothing."
- Upgrade idea: withdraw money from savings (needs a new table, ask Samia to add it to `schema.sql`).

### Hrishika - Expenses & Spending Limits
Read: `routes/expenses.py` (the `add_expense` function), `services/limits.py`, `static/app.js`, `tests/test_limits.py`.
- "Adding an expense is a short multi-step form on one route: check the input, ask for a limit if the category is new, show a caution if a limit or the budget would be exceeded, then save."
- "Category names ignore capital letters because the column uses `COLLATE NOCASE`."
- "The live caution is JavaScript calling `/api/check` while the user types; the server still checks again before saving."
- Upgrade ideas: edit-expense page; filter the expense list by category.

### Samia - Accounts, Dashboard, Reports & Database
Read: `schema.sql`, `db.py`, `services/common.py`, `routes/auth.py`, `routes/dashboard.py`, `tests/test_security_report.py`.
- "Passwords are stored only as hashes. Every query has `WHERE user_id = ?`, so users never see each other's data."
- "Forms are protected with a CSRF token; the database uses foreign keys and CHECK constraints."
- "The dashboard uses SQL `SUM` and `GROUP BY`. The Excel report is built with Pandas into three sheets."
- Upgrade ideas: change-password page; add a monthly-trend sheet to the Excel report; let `db.py` use PostgreSQL.

## Agreements between the three of you (do not break these)

| Who uses it | What | Owner |
|---|---|---|
| Samia's dashboard | `budget_row_for`, `budget_summary`, `pending_rollover`, `savings_total` | Rafi |
| Samia's dashboard | `category_rows` | Hrishika |
| Hrishika's add-expense | `budget_row_for` (to warn about the month budget) | Rafi |
| Everyone's pages | links with `url_for('<blueprint>.<function>')`, e.g. `budget.rollover`, `expenses.add_expense` | each owner |
| `base.html` (Rafi) | nav links to everyone's pages; logout button posts to `auth.logout` | Samia |
| Login page (Samia) | form fields `username`, `password`, `_csrf`; template variable `mode` | Samia |
| Every POST form | `<input type="hidden" name="_csrf" value="{{ csrf_token() }}">` | everyone |
| Money | always whole taka (integer); show with `{{ amount\|taka }}` | everyone |
| Database changes | new column or table goes into `schema.sql` | Samia (then delete your local `instance/` folder and run `seed.py`) |

If you rename a function in `services/`, tell the people in the table above first.

## Git workflow (PowerShell)

**Rafi** pushes the whole project once, as the starting point:

    git init
    git add .
    git commit -m "Initial TakaTrack app"
    git branch -M main
    git remote add origin <repo-url>
    git push -u origin main

**Hrishika and Samia** then:

    git clone <repo-url>
    cd <repo-folder>

**Everyone**, for each piece of work:

    git checkout main
    git pull
    git checkout -b feature/<short-name>        # e.g. feature/edit-expense
    # edit only your own files, run the tests
    git add <your files>
    git commit -m "Say clearly what you changed"
    git push -u origin feature/<short-name>     # then open a Pull Request on GitHub

Do not commit `.venv/` or `instance/` (already in `.gitignore`). Do not merge a Pull Request while a test fails.

## Run and test (Windows)

    py -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    .venv\Scripts\python.exe seed.py
    .venv\Scripts\python.exe -m flask --app app run
    .venv\Scripts\python.exe -m unittest discover -s tests -v

Demo login after `seed.py`: `demo` / `demo1234`.

## Honest note for interviews
The starting code was created with AI assistance. Say that openly, then explain **your own part** in detail:
what each of your files does, one thing you changed or added, and how it connects to your teammates' parts.
Do not describe a part you did not read.
