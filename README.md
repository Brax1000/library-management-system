# Library Management System

A Python library manager with a Windows Tkinter desktop application and a Vercel compatible web dashboard. The desktop version stores records in a local SQLite database.

## Features

- Dashboard statistics and recent loan activity, derived from SQLite.
- Book catalogue with search, availability filtering, add/edit/delete, ISBN uniqueness, and copy tracking.
- Borrower registration and lookup, duplicate membership protection, account eligibility.
- Atomic checkout with configurable default 14-day term and unique transaction IDs.
- Return processing, transaction history, overdue filtering and day-to-day recalculation.
- SQLite backup and restore controls.
- Vercel serverless dashboard and JSON endpoints; write routes require `LIBRARY_ADMIN_KEY`.
- Separate temporary database test suite; no network access or third-party packages required.

## Requirements and installation

Install Python 3.10 or newer for Windows and include the Tcl/Tk feature. Clone/download the project, then open a terminal in the project directory. No package installation is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Run

```powershell
python main.py
```

The application creates `data/library.db` on first launch. That local database is excluded from Git.

## Deploy on Vercel

Import the GitHub repository in Vercel. The Python function entrypoint is `api/index.py`; `main.py` also exports its handler so Vercel can detect the app. `vercel.json` routes the website and API paths to that function. No third-party Python dependencies are needed.

Set `LIBRARY_ADMIN_KEY` in Vercel Project Settings → Environment Variables to enable add, borrower registration, checkout, and return actions. Without it, the web app is read-only. The deployed default database is in `/tmp`, which is temporary serverless storage; records may disappear when a function instance is replaced. Connect a persistent database before storing real member records. The desktop app remains the persistent local SQLite version.

For local web preview, run `python api/index.py` and open `http://127.0.0.1:8000`. Use Vercel CLI with `vercel dev` to test rewrites locally.

## Tests

```powershell
python -m unittest discover -v
```

Tests use an isolated temporary database and do not touch the application's library data.

## Structure

`database/` contains schema and connection setup. `services/` holds validated business operations. `ui/` contains Tkinter pages and reusable table/form helpers. `utils/` contains validators. `tests/` tests core operations without the GUI.

## Database overview

The schema has books, borrowers, borrow_transactions, and settings tables, with foreign keys, unique ISBN/membership IDs, quantity checks, and indexes. Borrow/return updates use SQLite transactions so inventory and loan history stay consistent.

## Screenshots

Screenshots can be added here after running the app on Windows.

## Known limitations and future improvements

- The borrower page supports registration, editing, activation/deactivation, and search; transactions preserve each borrower's loan history.
- A native Windows desktop session is required to visually inspect Tkinter interactions.
- Future work: CSV reports, barcode scanning, and richer member profile views.
- The Vercel deployment uses temporary SQLite storage and has no built-in user login; protect writes with the admin key and do not store real borrower data until persistent storage and authentication are configured.

## License

MIT. See [LICENSE](LICENSE).

