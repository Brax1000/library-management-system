"""Desktop interface for the Library Management System."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path

NAVY='#14263d'; BLUE='#315c85'; BG='#f3f6fa'; WHITE='#ffffff'

class MainWindow:
    def __init__(self, root, service):
        self.root=root; self.s=service; self.root.title('Library Management System'); self.root.geometry('1180x760'); self.root.minsize(900,600); self.root.configure(bg=BG)
        style=ttk.Style(); style.theme_use('clam'); style.configure('Treeview',rowheight=30,font=('Segoe UI',10)); style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),background='#e6edf5'); style.configure('TButton',padding=7)
        self.side=tk.Frame(root,bg=NAVY,width=210); self.side.pack(side='left',fill='y'); self.side.pack_propagate(False)
        tk.Label(self.side,text='📚  LIBRARY\nMANAGEMENT',bg=NAVY,fg='white',font=('Segoe UI',15,'bold'),justify='left',pady=22).pack(fill='x')
        self.body=tk.Frame(root,bg=BG); self.body.pack(side='left',fill='both',expand=True)
        for label, page in [('Dashboard','dashboard'),('Books','books'),('Borrowers','borrowers'),('Borrow Books','checkout'),('Return Books','returns'),('Overdue Records','overdue'),('Transaction History','history'),('Settings','settings')]:
            tk.Button(self.side,text='  '+label,anchor='w',bg=NAVY,fg='white',activebackground=BLUE,activeforeground='white',relief='flat',font=('Segoe UI',11),pady=11,command=lambda p=page:self.show(p)).pack(fill='x')
        self.show('dashboard')

    def clear(self):
        for w in self.body.winfo_children(): w.destroy()
    def heading(self,title,subtitle='Manage your library records'):
        tk.Label(self.body,text=title,bg=BG,fg=NAVY,font=('Segoe UI',22,'bold')).pack(anchor='w',padx=26,pady=(24,2)); tk.Label(self.body,text=subtitle,bg=BG,fg='#66768a',font=('Segoe UI',10)).pack(anchor='w',padx=26,pady=(0,18))
    def show(self,page):
        self.clear(); getattr(self,'page_'+page)()
    def page_dashboard(self):
        self.heading('Library dashboard','A live view of your collection and lending activity'); d=self.s.dashboard()
        cards=tk.Frame(self.body,bg=BG); cards.pack(fill='x',padx=18)
        for i,(label,key,color) in enumerate([('Titles','books',BLUE),('Available copies','available','#16836b'),('On loan','borrowed','#bb7a22'),('Borrowers','borrowers','#6855a1'),('Overdue','overdue','#bd4b4b'),('Returned today','returned_today','#16836b')]):
            card=tk.Frame(cards,bg=WHITE,highlightbackground='#e1e7ef',highlightthickness=1); card.grid(row=0,column=i,sticky='ew',padx=7,pady=5); cards.columnconfigure(i,weight=1)
            tk.Label(card,text=label,bg=WHITE,fg='#6c7a8a',font=('Segoe UI',10)).pack(anchor='w',padx=14,pady=(12,3)); tk.Label(card,text=str(d[key]),bg=WHITE,fg=color,font=('Segoe UI',22,'bold')).pack(anchor='w',padx=14,pady=(0,12))
        self.table('Recent borrowing activity',[('transaction_id','Transaction'),('full_name','Borrower'),('title','Book'),('borrow_date','Borrowed'),('due_date','Due'),('display_status','Status')],d['recent'])
        self.table('Recent return activity',[('transaction_id','Transaction'),('full_name','Borrower'),('title','Book'),('return_date','Returned')],d['returns'])
        tk.Label(self.body,text='Most borrowed titles',bg=BG,fg=NAVY,font=('Segoe UI',13,'bold')).pack(anchor='w',padx=26,pady=(15,5))
        tk.Label(self.body,text='   •   '.join(f"{x['title']} ({x['loans']})" for x in d['popular']) or 'No loan history yet',bg=BG,fg='#42566e',font=('Segoe UI',10)).pack(anchor='w',padx=26)
    def table(self, title, columns, rows, actions=None):
        if title: tk.Label(self.body,text=title,bg=BG,fg=NAVY,font=('Segoe UI',13,'bold')).pack(anchor='w',padx=26,pady=(10,5))
        frame=tk.Frame(self.body,bg=WHITE); frame.pack(fill='both',expand=True,padx=26,pady=(0,14)); names=[x[0] for x in columns]; tree=ttk.Treeview(frame,columns=names,show='headings')
        for k, label in columns: tree.heading(k,text=label); tree.column(k,width=130,anchor='w')
        for row in rows: tree.insert('', 'end', values=[row.get(k,'') for k in names])
        y=ttk.Scrollbar(frame,orient='vertical',command=tree.yview); tree.configure(yscrollcommand=y.set); tree.pack(side='left',fill='both',expand=True); y.pack(side='right',fill='y'); self.tree=tree
        if actions: actions(tree)
        return tree
    def controls(self, placeholder, callback, filter_values=None):
        bar=tk.Frame(self.body,bg=BG); bar.pack(fill='x',padx=26,pady=(0,10)); ent=ttk.Entry(bar,width=38); ent.pack(side='left'); ent.insert(0,''); ent.bind('<KeyRelease>',lambda e:callback(ent.get(),filt.get() if filter_values else 'All'))
        filt=ttk.Combobox(bar,values=filter_values or [],state='readonly',width=16) if filter_values else None
        if filt: filt.set(filter_values[0]); filt.pack(side='left',padx=8); filt.bind('<<ComboboxSelected>>',lambda e:callback(ent.get(),filt.get()))
        ttk.Button(bar,text='Clear',command=lambda:(ent.delete(0,'end'),callback('',filt.get() if filt else 'All'))).pack(side='left',padx=6)
        return bar
    def form(self,title,fields,initial=None):
        win=tk.Toplevel(self.root); win.title(title); win.transient(self.root); win.grab_set(); entries={}
        for i,(key,label) in enumerate(fields):
            tk.Label(win,text=label,anchor='w').grid(row=i,column=0,padx=14,pady=7,sticky='w'); e=ttk.Entry(win,width=38); e.grid(row=i,column=1,padx=14,pady=7); e.insert(0,(initial or {}).get(key,'') or ''); entries[key]=e
        result={}
        def save(): result.update({k:e.get().strip() for k,e in entries.items()}); win.destroy()
        ttk.Button(win,text='Save',command=save).grid(row=len(fields),column=1,padx=14,pady=14,sticky='e'); win.wait_window(); return result or None
    def page_books(self):
        self.heading('Books','Search and maintain your collection'); bar=self.controls('Search books',lambda q,f:refresh(q,f),['All','Available','Unavailable']); ttk.Button(bar,text='+ Add book',command=lambda:edit()).pack(side='right'); cols=[('book_id','ID'),('isbn','ISBN'),('title','Title'),('author','Author'),('category','Category'),('total_copies','Copies'),('available_copies','Available')]
        tree=self.table('Collection',cols,[])
        def refresh(q='',f='All'):
            for i in tree.get_children():tree.delete(i)
            for row in self.s.books(q,f):tree.insert('','end',values=[row[x] for x,_ in cols])
        def edit(existing=None):
            fields=[('isbn','ISBN'),('title','Title'),('author','Author'),('publisher','Publisher'),('publication_year','Publication year'),('category','Category'),('total_copies','Total copies'),('available_copies','Available copies')]; data=self.form('Book details',fields,existing)
            if data:
                try:self.s.add_book(data,existing['book_id'] if existing else None); refresh()
                except Exception as e:messagebox.showerror('Could not save book',str(e))
        def edit_sel():
            if tree.selection():
                book_id=tree.item(tree.selection()[0])['values'][0]
                record=next((x for x in self.s.books() if x['book_id']==book_id),None)
                if record: edit(record)
        def delete_sel():
            if tree.selection() and messagebox.askyesno('Delete book','Delete selected book?'):
                try:self.s.delete_book(tree.item(tree.selection()[0])['values'][0]);refresh()
                except Exception as e:messagebox.showerror('Could not delete',str(e))
        ttk.Button(bar,text='Edit selected',command=edit_sel).pack(side='right',padx=5); ttk.Button(bar,text='Delete selected',command=delete_sel).pack(side='right',padx=5)
        def refresh_start():refresh('', 'All')
        refresh_start()
    def page_borrowers(self):
        self.heading('Borrowers','Manage membership accounts and eligibility'); bar=self.controls('Search borrowers',lambda q,f:refresh(q),None); ttk.Button(bar,text='+ Register borrower',command=lambda:edit()).pack(side='right'); cols=[('borrower_id','ID'),('full_name','Full name'),('membership_id','Membership ID'),('contact_number','Contact'),('email','Email'),('account_status','Status')]; tree=self.table('Members',cols,[])
        def refresh(q=''):
            for i in tree.get_children():tree.delete(i)
            for r in self.s.borrowers(q):tree.insert('','end',values=[r[x] for x,_ in cols])
        def edit(existing=None):
            fields=[('full_name','Full name'),('membership_id','Membership ID'),('contact_number','Contact number'),('email','Email address')]
            if existing: fields.append(('account_status','Status (Active/Inactive)'))
            d=self.form('Borrower details',fields,existing)
            if d:
                try:self.s.add_borrower(d,existing['borrower_id'] if existing else None);refresh()
                except Exception as e:messagebox.showerror('Could not save borrower',str(e))
        def edit_sel():
            if tree.selection():
                vals=tree.item(tree.selection()[0])['values']; edit(dict(zip([x[0] for x in cols],vals)))
        ttk.Button(bar,text='Edit selected',command=edit_sel).pack(side='right',padx=5)
        def profile(_event=None):
            if not tree.selection(): return
            borrower_id=tree.item(tree.selection()[0])['values'][0]
            records=[r for r in self.s.transactions() if r['borrower_id']==borrower_id]
            summary='\n'.join(f"{r['title']} — {r['display_status']} (due {r['due_date']})" for r in records) or 'No borrowing history.'
            messagebox.showinfo('Borrower history',summary)
        tree.bind('<Double-1>',profile)
        refresh()
    def page_checkout(self):
        self.heading('Borrow books','Select a registered member and an available title'); borrowers=self.s.borrowers(); books=self.s.books(availability='Available'); b=ttk.Combobox(self.body,state='readonly',values=[f"{x['borrower_id']} — {x['full_name']} ({x['account_status']})" for x in borrowers]); b.pack(anchor='w',padx=30,pady=5); bk=ttk.Combobox(self.body,state='readonly',values=[f"{x['book_id']} — {x['title']} ({x['available_copies']} available)" for x in books]); bk.pack(anchor='w',padx=30,pady=5)
        def go():
            try:tid=self.s.checkout(int(b.get().split(' — ')[0]),int(bk.get().split(' — ')[0]));messagebox.showinfo('Loan recorded',f'Transaction {tid} recorded.');self.show('checkout')
            except Exception as e:messagebox.showerror('Could not borrow',str(e))
        ttk.Button(self.body,text='Record borrowing',command=go).pack(anchor='w',padx=30,pady=12)
    def page_returns(self):self.transaction_page('Active',True)
    def page_overdue(self):self.transaction_page('Overdue')
    def page_history(self):self.transaction_page('All')
    def transaction_page(self,mode,can_return=False):
        self.heading({'Active':'Return books','Overdue':'Overdue records','All':'Transaction history'}[mode]); cols=[('transaction_id','Transaction'),('full_name','Borrower'),('title','Book'),('borrow_date','Borrowed'),('due_date','Due date'),('return_date','Returned'),('display_status','Status')]; tree=self.table('Transactions',cols,[]); bar=self.controls('Search transactions',lambda q,f:refresh(q),None)
        def refresh(q=''):
            for i in tree.get_children():tree.delete(i)
            for r in self.s.transactions(q,mode):tree.insert('','end',values=[r.get(x,'') or '' for x,_ in cols],tags=('overdue',) if r['display_status']=='Overdue' else ())
            tree.tag_configure('overdue',foreground='#bd4b4b')
        if can_return:
            def ret():
                if tree.selection():
                    try:self.s.return_book(tree.item(tree.selection()[0])['values'][0]);refresh()
                    except Exception as e:messagebox.showerror('Could not return book',str(e))
            ttk.Button(bar,text='Process return',command=ret).pack(side='right')
        refresh()
    def page_settings(self):
        self.heading('Settings','Loan period and local database backup'); tk.Label(self.body,text='Borrowing period (days)',bg=BG).pack(anchor='w',padx=30); e=ttk.Entry(self.body); e.insert(0,'14'); e.pack(anchor='w',padx=30,pady=5); ttk.Button(self.body,text='Save borrowing period',command=lambda:self._period(e.get())).pack(anchor='w',padx=30,pady=5)
        ttk.Button(self.body,text='Back up database',command=self._backup).pack(anchor='w',padx=30,pady=5); ttk.Button(self.body,text='Restore database backup',command=self._restore).pack(anchor='w',padx=30,pady=5)
    def _period(self,v):
        try:self.s.set_period(v);messagebox.showinfo('Settings saved','Borrowing period updated.')
        except Exception as e:messagebox.showerror('Invalid setting',str(e))
    def _backup(self):
        p=filedialog.asksaveasfilename(defaultextension='.db',filetypes=[('SQLite database','*.db')]);
        if p:
            try:self.s.backup(p);messagebox.showinfo('Backup complete','Database backup saved.')
            except Exception as e:messagebox.showerror('Backup failed',str(e))
    def _restore(self):
        p=filedialog.askopenfilename(filetypes=[('SQLite database','*.db')]);
        if p and messagebox.askyesno('Restore backup','This replaces the current library database. Continue?'):
            try:self.s.restore(p);messagebox.showinfo('Restore complete','Restart the page to load restored data.')
            except Exception as e:messagebox.showerror('Restore failed',str(e))

