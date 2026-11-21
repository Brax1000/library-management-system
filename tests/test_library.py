import tempfile
import unittest
from pathlib import Path
from database.connection import initialize
from services.library_service import LibraryService

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'test.db'; initialize(self.path); self.s=LibraryService(self.path)
    def tearDown(self): self.tmp.cleanup()
    def book(self, copies=2):
        self.s.add_book(dict(isbn='978-1',title='Python',author='A. Writer',category='Tech',total_copies=copies,available_copies=copies)); return self.s.books()[0]['book_id']
    def borrower(self):
        self.s.add_borrower(dict(full_name='Test Member',membership_id='M-1',email='m@example.com')); return self.s.borrowers()[0]['borrower_id']
    def test_unique_isbn_and_quantity_validation(self):
        self.book()
        with self.assertRaises(ValueError): self.s.add_book(dict(isbn='978-1',title='Other',author='A',category='Tech',total_copies=1,available_copies=1))
        with self.assertRaises(ValueError): self.s.add_book(dict(isbn='2',title='Other',author='A',category='Tech',total_copies=0,available_copies=1))
    def test_checkout_return_and_duplicate_return(self):
        bid=self.book(); uid=self.borrower(); tid=self.s.checkout(uid,bid)
        self.assertEqual(self.s.books()[0]['available_copies'],1)
        self.s.return_book(tid); self.assertEqual(self.s.books()[0]['available_copies'],2)
        with self.assertRaises(ValueError): self.s.return_book(tid)
        self.assertEqual(self.s.transactions()[0]['status'],'Returned')
    def test_unavailable_and_inactive_borrower_rejected(self):
        bid=self.book(0); uid=self.borrower()
        with self.assertRaises(ValueError): self.s.checkout(uid,bid)
        self.s.add_borrower(dict(full_name='Test Member',membership_id='M-1',account_status='Inactive'),uid)
        with self.assertRaises(ValueError): self.s.checkout(uid,bid)
    def test_duplicate_membership_and_overdue(self):
        uid=self.borrower(); bid=self.book()
        with self.assertRaises(ValueError): self.s.add_borrower(dict(full_name='Other',membership_id='M-1'))
        tid=self.s.checkout(uid,bid)
        from database.connection import connect
        with connect(self.path) as db: db.execute("UPDATE borrow_transactions SET due_date='2000-01-01' WHERE transaction_id=?",(tid,))
        self.assertEqual(len(self.s.transactions(mode='Overdue')),1)
        self.assertEqual(self.s.dashboard()['overdue'],1)
    def test_delete_guard_and_period(self):
        bid=self.book(); uid=self.borrower(); self.s.checkout(uid,bid)
        with self.assertRaises(ValueError): self.s.delete_book(bid)
        self.s.set_period(30)
        self.assertEqual(self.s.rows("SELECT setting_value FROM settings WHERE setting_key='borrowing_period'")[0]['setting_value'],'30')

if __name__=='__main__': unittest.main()

