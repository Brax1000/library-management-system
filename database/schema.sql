PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS books (
 book_id INTEGER PRIMARY KEY, isbn TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
 author TEXT NOT NULL, publisher TEXT DEFAULT '', publication_year INTEGER,
 category TEXT NOT NULL, total_copies INTEGER NOT NULL CHECK(total_copies >= 0),
 available_copies INTEGER NOT NULL CHECK(available_copies >= 0 AND available_copies <= total_copies),
 date_added TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS borrowers (
 borrower_id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, membership_id TEXT NOT NULL UNIQUE,
 contact_number TEXT DEFAULT '', email TEXT DEFAULT '', registration_date TEXT NOT NULL,
 account_status TEXT NOT NULL DEFAULT 'Active' CHECK(account_status IN ('Active','Inactive')));
CREATE TABLE IF NOT EXISTS borrow_transactions (
 transaction_id TEXT PRIMARY KEY, borrower_id INTEGER NOT NULL REFERENCES borrowers(borrower_id),
 book_id INTEGER NOT NULL REFERENCES books(book_id), borrow_date TEXT NOT NULL, due_date TEXT NOT NULL,
 return_date TEXT, status TEXT NOT NULL CHECK(status IN ('Borrowed','Overdue','Returned')));
CREATE TABLE IF NOT EXISTS settings (setting_id INTEGER PRIMARY KEY, setting_key TEXT NOT NULL UNIQUE, setting_value TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_tx_status_due ON borrow_transactions(status,due_date);
CREATE INDEX IF NOT EXISTS idx_tx_borrower ON borrow_transactions(borrower_id);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
INSERT OR IGNORE INTO settings(setting_key,setting_value) VALUES('borrowing_period','14');

