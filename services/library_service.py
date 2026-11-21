"""Validated library operations backed by SQLite."""
import uuid
from datetime import date, timedelta
from database.connection import connect
from utils.validators import required, email, year, quantity

class LibraryService:
    def __init__(self, db_path): self.db_path = db_path

    def rows(self, sql, params=()):
        with connect(self.db_path) as db: return [dict(x) for x in db.execute(sql, params)]

    def add_book(self, data, book_id=None):
        d = dict(data); d['isbn']=required(d.get('isbn'),'ISBN'); d['title']=required(d.get('title'),'Title')
        d['author']=required(d.get('author'),'Author'); d['category']=required(d.get('category'),'Category')
        d['total_copies']=quantity(d.get('total_copies',1)); d['available_copies']=quantity(d.get('available_copies',d['total_copies']))
        d['publication_year']=year(d.get('publication_year'))
        if d['available_copies'] > d['total_copies']: raise ValueError('Available copies cannot exceed total copies.')
        try:
            with connect(self.db_path) as db:
                if book_id:
                    borrowed=db.execute("SELECT COUNT(*) FROM borrow_transactions WHERE book_id=? AND status!='Returned'",(book_id,)).fetchone()[0]
                    if d['total_copies'] < borrowed: raise ValueError('Total copies cannot be lower than the number currently on loan.')
                    d['available_copies'] = d['total_copies'] - borrowed
                    db.execute('UPDATE books SET isbn=?,title=?,author=?,publisher=?,publication_year=?,category=?,total_copies=?,available_copies=? WHERE book_id=?',(d['isbn'],d['title'],d['author'],d.get('publisher',''),d['publication_year'],d['category'],d['total_copies'],d['available_copies'],book_id))
                else:
                    db.execute('INSERT INTO books(isbn,title,author,publisher,publication_year,category,total_copies,available_copies,date_added) VALUES(?,?,?,?,?,?,?,?,?)',(d['isbn'],d['title'],d['author'],d.get('publisher',''),d['publication_year'],d['category'],d['total_copies'],d['available_copies'],date.today().isoformat()))
        except Exception as e:
            if 'UNIQUE' in str(e): raise ValueError('That ISBN is already registered.')
            raise

    def delete_book(self, book_id):
        with connect(self.db_path) as db:
            if db.execute("SELECT 1 FROM borrow_transactions WHERE book_id=? AND status!='Returned'",(book_id,)).fetchone(): raise ValueError('Cannot delete a book with active loans.')
            if db.execute('DELETE FROM books WHERE book_id=?',(book_id,)).rowcount == 0: raise ValueError('Book not found.')

    def add_borrower(self, d, borrower_id=None):
        name=required(d.get('full_name'),'Full name'); mid=required(d.get('membership_id'),'Membership ID'); em=email(d.get('email'))
        try:
            with connect(self.db_path) as db:
                if borrower_id: db.execute('UPDATE borrowers SET full_name=?,membership_id=?,contact_number=?,email=?,account_status=? WHERE borrower_id=?',(name,mid,d.get('contact_number',''),em,d.get('account_status','Active'),borrower_id))
                else: db.execute('INSERT INTO borrowers(full_name,membership_id,contact_number,email,registration_date) VALUES(?,?,?,?,?)',(name,mid,d.get('contact_number',''),em,date.today().isoformat()))
        except Exception as e:
            if 'UNIQUE' in str(e): raise ValueError('That membership ID is already registered.')
            raise

    def checkout(self, borrower_id, book_id):
        with connect(self.db_path) as db:
            b=db.execute('SELECT account_status FROM borrowers WHERE borrower_id=?',(borrower_id,)).fetchone()
            book=db.execute('SELECT available_copies FROM books WHERE book_id=?',(book_id,)).fetchone()
            if not b: raise ValueError('Borrower not found.')
            if b['account_status']!='Active': raise ValueError('This borrower account is inactive.')
            if not book or book['available_copies']<1: raise ValueError('No copies are available.')
            period=int(db.execute("SELECT setting_value FROM settings WHERE setting_key='borrowing_period'").fetchone()[0])
            now=date.today(); tid=uuid.uuid4().hex[:12].upper()
            db.execute('UPDATE books SET available_copies=available_copies-1 WHERE book_id=? AND available_copies>0',(book_id,))
            db.execute('INSERT INTO borrow_transactions VALUES(?,?,?,?,?,?,?)',(tid,borrower_id,book_id,now.isoformat(),(now+timedelta(days=period)).isoformat(),None,'Borrowed'))
            return tid

    def return_book(self, tid):
        with connect(self.db_path) as db:
            tx=db.execute("SELECT book_id,status FROM borrow_transactions WHERE transaction_id=?",(tid,)).fetchone()
            if not tx or tx['status']=='Returned': raise ValueError('Active transaction not found.')
            db.execute("UPDATE borrow_transactions SET status='Returned',return_date=? WHERE transaction_id=?",(date.today().isoformat(),tid))
            db.execute('UPDATE books SET available_copies=available_copies+1 WHERE book_id=?',(tx['book_id'],))

    def set_period(self, days):
        days=quantity(days)
        if days<1 or days>365: raise ValueError('Borrowing period must be between 1 and 365 days.')
        with connect(self.db_path) as db: db.execute("UPDATE settings SET setting_value=? WHERE setting_key='borrowing_period'",(str(days),))

    def backup(self, target):
        import sqlite3
        src=sqlite3.connect(self.db_path); dest=sqlite3.connect(str(target))
        try: src.backup(dest)
        finally: dest.close(); src.close()

    def restore(self, source):
        import sqlite3
        src=sqlite3.connect(str(source)); dest=sqlite3.connect(self.db_path)
        try: src.backup(dest)
        finally: dest.close(); src.close()

    def books(self, query='', availability='All'):
        q=f'%{query.strip()}%'; sql='SELECT * FROM books WHERE (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)'; p=[q]*4
        if availability=='Available': sql+=' AND available_copies>0'
        elif availability=='Unavailable': sql+=' AND available_copies=0'
        return self.rows(sql+' ORDER BY title COLLATE NOCASE',p)

    def borrowers(self, query=''):
        q=f'%{query.strip()}%'; return self.rows('SELECT * FROM borrowers WHERE full_name LIKE ? OR membership_id LIKE ? OR CAST(borrower_id AS TEXT) LIKE ? ORDER BY full_name',(q,q,q))

    def transactions(self, query='', mode='All'):
        q=f'%{query.strip()}%'; sql="SELECT t.*,CASE WHEN t.status!='Returned' AND t.due_date<? THEN 'Overdue' ELSE t.status END AS display_status,b.title,br.full_name,br.membership_id FROM borrow_transactions t JOIN books b USING(book_id) JOIN borrowers br USING(borrower_id) WHERE (t.transaction_id LIKE ? OR b.title LIKE ? OR br.full_name LIKE ? OR t.status LIKE ? OR br.membership_id LIKE ?)"; p=[date.today().isoformat(),q,q,q,q,q]
        if mode=='Active': sql+=" AND t.status!='Returned'"
        elif mode=='Overdue': sql+=" AND t.status!='Returned' AND t.due_date<?"; p.append(date.today().isoformat())
        return self.rows(sql+' ORDER BY t.borrow_date DESC',p)

    def dashboard(self):
        with connect(self.db_path) as db:
            stats={k:db.execute(sql).fetchone()[0] for k,sql in {'books':'SELECT COUNT(*) FROM books','available':'SELECT COALESCE(SUM(available_copies),0) FROM books','borrowed':"SELECT COUNT(*) FROM borrow_transactions WHERE status!='Returned'",'borrowers':'SELECT COUNT(*) FROM borrowers','overdue':"SELECT COUNT(*) FROM borrow_transactions WHERE status!='Returned' AND due_date<?"}.items() if k!='overdue'}
            stats['overdue']=db.execute("SELECT COUNT(*) FROM borrow_transactions WHERE status!='Returned' AND due_date<?",(date.today().isoformat(),)).fetchone()[0]
            stats['popular']=[dict(r) for r in db.execute('SELECT b.title,COUNT(*) AS loans FROM borrow_transactions t JOIN books b USING(book_id) GROUP BY b.book_id ORDER BY loans DESC LIMIT 5')]
            stats['returned_today']=db.execute("SELECT COUNT(*) FROM borrow_transactions WHERE return_date=?",(date.today().isoformat(),)).fetchone()[0]
            stats['returns']=[dict(r) for r in db.execute('SELECT t.*,b.title,br.full_name,br.membership_id FROM borrow_transactions t JOIN books b USING(book_id) JOIN borrowers br USING(borrower_id) WHERE t.return_date=? ORDER BY t.return_date DESC LIMIT 8',(date.today().isoformat(),))]
            stats['recent']=self.transactions()[:8]
            return stats

