import os
import tempfile
import unittest
from pathlib import Path

from database.connection import initialize
from services.library_service import LibraryService
from api import index


class VercelAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'web.db'
        initialize(self.path)
        self.previous_service = index.service
        self.previous_key = os.environ.pop('LIBRARY_ADMIN_KEY', None)
        index.service = LibraryService(self.path)

    def tearDown(self):
        index.service = self.previous_service
        os.environ.pop('LIBRARY_ADMIN_KEY', None)
        if self.previous_key:
            os.environ['LIBRARY_ADMIN_KEY'] = self.previous_key
        self.tmp.cleanup()

    def test_health_and_homepage(self):
        status, data = index.dispatch('GET', '/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('Library Desk', index.PAGE)

    def test_writes_require_configured_key(self):
        payload = {'isbn': '123', 'title': 'Test', 'author': 'Writer', 'category': 'General', 'total_copies': 1}
        status, _ = index.dispatch('POST', '/api/books', payload)
        self.assertEqual(status, 503)
        os.environ['LIBRARY_ADMIN_KEY'] = 'test-secret'
        self.assertEqual(index.dispatch('POST', '/api/books', payload, 'wrong-key')[0], 401)
        self.assertEqual(index.dispatch('POST', '/api/books', payload, 'test-secret')[0], 201)
        self.assertEqual(len(index.service.books()), 1)

    def test_checkout_and_return_api(self):
        os.environ['LIBRARY_ADMIN_KEY'] = 'test-secret'
        index.service.add_book({'isbn': '456', 'title': 'Book', 'author': 'Writer', 'category': 'General', 'total_copies': 1})
        index.service.add_borrower({'full_name': 'Member', 'membership_id': 'M-1'})
        book_id = index.service.books()[0]['book_id']
        borrower_id = index.service.borrowers()[0]['borrower_id']
        status, transaction = index.dispatch('POST', '/api/checkout', {'book_id': book_id, 'borrower_id': borrower_id}, 'test-secret')
        self.assertEqual(status, 201)
        self.assertEqual(index.service.books()[0]['available_copies'], 0)
        self.assertEqual(index.dispatch('POST', '/api/returns', {'transaction_id': transaction['transaction_id']}, 'test-secret')[0], 200)
        self.assertEqual(index.service.books()[0]['available_copies'], 1)


if __name__ == '__main__':
    unittest.main()

