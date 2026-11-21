"""Desktop launcher and Vercel-compatible HTTP entrypoint."""
from api.index import handler

def main():
    import tkinter as tk
    from config import DATABASE_PATH
    from database.connection import initialize
    from services.library_service import LibraryService
    from ui.main_window import MainWindow

    initialize(DATABASE_PATH)
    root=tk.Tk(); MainWindow(root,LibraryService(DATABASE_PATH)); root.mainloop()

if __name__=='__main__': main()

