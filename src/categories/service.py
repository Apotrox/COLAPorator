import sqlite3

class CategoryService:
    def __init__(self, db):
        self.db = db