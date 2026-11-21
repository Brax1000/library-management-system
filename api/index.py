"""Dependency-free HTTP application for Vercel Python Functions."""
import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from database.connection import initialize
from services.library_service import LibraryService

if os.environ.get('LIBRARY_DATABASE_PATH'):
    DB_PATH = Path(os.environ['LIBRARY_DATABASE_PATH'])
elif os.environ.get('VERCEL'):
    DB_PATH = Path('/tmp/library.db')
else:
    DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'library.db'

initialize(DB_PATH)
service = LibraryService(DB_PATH)

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Library Desk</title><style>
:root{color-scheme:light;--navy:#14263d;--blue:#315c85;--bg:#f3f6fa;--muted:#607086;--line:#e1e7ef}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#1d2b3c;font:15px system-ui,Segoe UI,sans-serif}.shell{max-width:1180px;margin:auto;padding:28px}.head{display:flex;justify-content:space-between;align-items:center;gap:20px}.brand{color:var(--navy);font-size:25px;font-weight:750}.sub,.muted{color:var(--muted)}.banner{margin:18px 0;padding:12px 15px;border-radius:10px;background:#fff4d6;color:#715719}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px;margin:20px 0}.card,.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:17px}.card span{display:block;color:var(--muted);font-size:13px}.card strong{display:block;color:var(--navy);font-size:27px;margin-top:6px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.panel h2{font-size:17px;margin:0 0 14px;color:var(--navy)}input,select,button{font:inherit;border:1px solid #cad4df;border-radius:8px;padding:9px 11px;background:white}input{width:min(100%,360px)}button{cursor:pointer;background:var(--blue);border-color:var(--blue);color:white}button.secondary{background:white;color:var(--blue)}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:9px 7px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:12px}.scroll{overflow:auto;max-height:360px}.status{font-weight:650}.overdue{color:#b64242}.empty{padding:20px;text-align:center;color:var(--muted)}dialog{border:0;border-radius:14px;padding:22px;box-shadow:0 12px 40px #10203040;width:min(480px,94vw)}dialog form{display:grid;gap:10px}dialog input,dialog select{width:100%}dialog::backdrop{background:#10203070}.notice{margin-top:18px;color:var(--muted);font-size:12px}@media(max-width:760px){.shell{padding:16px}.grid{grid-template-columns:1fr}.head{align-items:flex-start;flex-direction:column}}
</style></head><body><main class="shell"><header class="head"><div><div class="brand">📚 Library Desk</div><div class="sub">Books, members, loans, and returns</div></div><div class="toolbar"><input id="search" placeholder="Search books" aria-label="Search books"><button class="secondary" onclick="refresh()">Refresh</button><button id="borrowBook" onclick="openForm('checkout')">Borrow book</button><button id="addBook" onclick="openForm('book')">Add book</button></div></header>
<div class="banner" id="storageBanner">This deployment uses temporary storage. Records can be lost when the server restarts. Connect a persistent database before using real library data.</div>
<section class="cards" id="cards"></section><section class="grid"><article class="panel"><h2>Book collection</h2><div class="scroll"><table><thead><tr><th>ISBN</th><th>Title</th><th>Author</th><th>Available</th></tr></thead><tbody id="books"></tbody></table></div></article><article class="panel"><h2>Current loans and overdue books</h2><div class="scroll"><table><thead><tr><th>Borrower</th><th>Book</th><th>Due</th><th>Status</th><th></th></tr></thead><tbody id="loans"></tbody></table></div></article><article class="panel"><h2>Borrowers</h2><div class="toolbar"><button id="addBorrower" onclick="openForm('borrower')">Register borrower</button></div><div class="scroll"><table><thead><tr><th>Name</th><th>Member ID</th><th>Account</th></tr></thead><tbody id="borrowers"></tbody></table></div></article><article class="panel"><h2>Popular books</h2><div id="popular" class="muted">Loading…</div></article></section><p class="notice">Write actions require the <code>LIBRARY_ADMIN_KEY</code> environment variable in Vercel and a key entered when prompted. This demo has no sign-in system.</p></main>
<dialog id="dialog"><form id="form"><h2 id="formTitle"></h2><div id="fields"></div><div class="toolbar"><button type="submit">Save</button><button type="button" class="secondary" onclick="dialog.close()">Cancel</button></div></form></dialog>
<script>
const $=s=>document.querySelector(s);let books=[],borrowers=[],loans=[],adminKey=sessionStorage.getItem('libraryAdminKey')||'';
async function api(path,options={}){let headers={'Content-Type':'application/json',...(options.headers||{})};if(adminKey)headers['X-Library-Admin-Key']=adminKey;let r=await fetch(path,{...options,headers});let d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
function rows(el,html,empty){$(el).innerHTML=html||`<tr><td colspan="8" class="empty">${empty}</td></tr>`}
async function refresh(){try{let [d,b,u,t]=await Promise.all([api('/api/dashboard'),api('/api/books?q='+encodeURIComponent($('#search').value)),api('/api/borrowers'),api('/api/transactions?mode=Active')]);books=b;borrowers=u;loans=t;$('#cards').innerHTML=[['Titles',d.books],['Available copies',d.available],['On loan',d.borrowed],['Borrowers',d.borrowers],['Overdue',d.overdue],['Returned today',d.returned_today]].map(x=>`<div class="card"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join('');rows('#books',books.map(x=>`<tr><td>${esc(x.isbn)}</td><td>${esc(x.title)}</td><td>${esc(x.author)}</td><td>${x.available_copies} / ${x.total_copies}</td></tr>`).join(''),'No books yet.');rows('#borrowers',borrowers.map(x=>`<tr><td>${esc(x.full_name)}</td><td>${esc(x.membership_id)}</td><td>${esc(x.account_status)}</td></tr>`).join(''),'No borrowers yet.');rows('#loans',loans.map(x=>`<tr><td>${esc(x.full_name)}</td><td>${esc(x.title)}</td><td>${esc(x.due_date)}</td><td class="status ${x.display_status==='Overdue'?'overdue':''}">${esc(x.display_status)}</td><td><button class="secondary" onclick="returnBook('${esc(x.transaction_id)}')">Return</button></td></tr>`).join(''),'No active loans.');$('#popular').innerHTML=d.popular.map(x=>`<p>${esc(x.title)} <span class="muted">· ${x.loans} loans</span></p>`).join('')||'No loan history yet.';$('#storageBanner').hidden=!d.temporary_storage;$('#addBook').disabled=$('#addBorrower').disabled=$('#borrowBook').disabled=!d.writes_enabled;}catch(e){alert(e.message)}}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function openForm(kind){let fields=kind==='book'?[['isbn','ISBN'],['title','Title'],['author','Author'],['category','Category'],['publisher','Publisher'],['publication_year','Publication year'],['total_copies','Total copies']]:kind==='borrower'?[['full_name','Full name'],['membership_id','Membership ID'],['contact_number','Contact number'],['email','Email']]:[['borrower_id','Borrower'],['book_id','Book']];$('#formTitle').textContent=kind==='book'?'Add book':kind==='borrower'?'Register borrower':'Borrow a book';$('#fields').innerHTML=fields.map(([n,l])=>{if(kind==='checkout')return `<label>${l}<select name="${n}" required>${(n==='borrower_id'?borrowers.filter(x=>x.account_status==='Active').map(x=>[x.borrower_id,x.full_name]):books.filter(x=>x.available_copies>0).map(x=>[x.book_id,x.title+' ('+x.available_copies+' available)'])).map(([v,t])=>`<option value="${v}">${esc(t)}</option>`).join('')}</select></label>`;return `<label>${l}<input name="${n}" ${['isbn','title','author','category','full_name','membership_id'].includes(n)?'required':''}></label>`}).join('');$('#form').onsubmit=async e=>{e.preventDefault();try{const body=Object.fromEntries(new FormData(e.target));if(!adminKey){adminKey=prompt('Enter your library admin key');if(!adminKey)return;sessionStorage.setItem('libraryAdminKey',adminKey)}await api('/api/'+(kind==='book'?'books':kind==='borrower'?'borrowers':'checkout'),{method:'POST',body:JSON.stringify(body)});dialog.close();refresh()}catch(err){alert(err.message)}};dialog.showModal()}
async function returnBook(id){if(!adminKey){adminKey=prompt('Enter your library admin key');if(!adminKey)return;sessionStorage.setItem('libraryAdminKey',adminKey)}try{await api('/api/returns',{method:'POST',body:JSON.stringify({transaction_id:id})});refresh()}catch(e){alert(e.message)}}
$('#search').addEventListener('input',()=>refresh());refresh();
</script></body></html>'''

def _json(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

def dispatch(method, path, payload=None, admin_key=None):
    """Route API requests; kept separate for unit testing."""
    payload = payload or {}
    if method == 'GET' and path == '/api/health':
        return 200, {'status': 'ok', 'framework': 'Vercel Python Functions'}
    if method == 'GET' and path == '/api/dashboard':
        data = service.dashboard()
        data['temporary_storage'] = bool(os.environ.get('VERCEL')) and not os.environ.get('LIBRARY_DATABASE_PATH')
        data['writes_enabled'] = bool(os.environ.get('LIBRARY_ADMIN_KEY'))
        return 200, data
    if method == 'GET' and path == '/api/books':
        return 200, service.books(urlparse(path).query)  # Empty query; handler supplies filtering below.
    if method == 'GET' and path == '/api/borrowers':
        return 200, service.borrowers()
    if method == 'GET' and path == '/api/transactions':
        return 200, service.transactions()
    if method in ('POST', 'DELETE') and not os.environ.get('LIBRARY_ADMIN_KEY'):
        return 503, {'error': 'Write access is disabled. Configure LIBRARY_ADMIN_KEY in the Vercel project settings.'}
    if method in ('POST', 'DELETE') and (not admin_key or admin_key != os.environ['LIBRARY_ADMIN_KEY']):
        return 401, {'error': 'A valid library admin key is required.'}
    if method == 'POST' and path == '/api/books':
        service.add_book(payload)
        return 201, {'ok': True}
    if method == 'POST' and path == '/api/borrowers':
        service.add_borrower(payload)
        return 201, {'ok': True}
    if method == 'POST' and path == '/api/checkout':
        return 201, {'transaction_id': service.checkout(int(payload['borrower_id']), int(payload['book_id']))}
    if method == 'POST' and path == '/api/returns':
        service.return_book(payload['transaction_id'])
        return 200, {'ok': True}
    return 404, {'error': 'Route not found.'}

class handler(BaseHTTPRequestHandler):
    """Vercel HTTP function entrypoint."""
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html', '/api/index'):
            body = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == '/api/books':
            from urllib.parse import parse_qs
            query = parse_qs(urlparse(self.path).query).get('q', [''])[0]
            return _json(self, 200, service.books(query))
        if path == '/api/transactions':
            from urllib.parse import parse_qs
            mode = parse_qs(urlparse(self.path).query).get('mode', ['All'])[0]
            return _json(self, 200, service.transactions(mode=mode))
        try:
            status, data = dispatch('GET', path)
            return _json(self, status, data)
        except Exception:
            return _json(self, 500, {'error': 'Could not load library data.'})

    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size > 100_000:
                return _json(self, 413, {'error': 'Request is too large.'})
            payload = json.loads(self.rfile.read(size) or b'{}')
            status, data = dispatch('POST', urlparse(self.path).path, payload, self.headers.get('X-Library-Admin-Key'))
            return _json(self, status, data)
        except ValueError as exc:
            return _json(self, 400, {'error': str(exc)})
        except (KeyError, TypeError, json.JSONDecodeError):
            return _json(self, 400, {'error': 'Invalid request data.'})
        except Exception:
            return _json(self, 500, {'error': 'Could not save the requested record.'})

if __name__ == '__main__':
    from http.server import HTTPServer
    HTTPServer(('127.0.0.1', 8000), handler).serve_forever()

