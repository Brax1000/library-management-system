# Library Management System

A local Windows desktop application for managing a library collection, members, loans, returns, and overdue items. The interface uses Tkinter/ttk and all application records are stored in SQLite.

## Features

- Dashboard statistics and recent loan activity, derived from SQLite.
- Book catalogue with search, availability filtering, add/edit/delete, ISBN uniqueness, and copy tracking.
- Borrower registration and lookup, duplicate membership protection, account eligibility.
- Atomic checkout with configurable default 14-day term and unique transaction IDs.
- Return processing, transaction history, overdue filtering and day-to-day recalculation.
- SQLite backup and restore controls.
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

## License

MIT. See [LICENSE](LICENSE).
