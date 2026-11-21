"""Launch the Library Management System desktop application."""
import tkinter as tk
from config import DATABASE_PATH
from database.connection import initialize
from services.library_service import LibraryService
from ui.main_window import MainWindow

def main():
    initialize(DATABASE_PATH)
    root=tk.Tk(); MainWindow(root,LibraryService(DATABASE_PATH)); root.mainloop()

if __name__=='__main__': main()

