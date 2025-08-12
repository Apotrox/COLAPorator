import sqlite3
from typing import List
from .Category import Category

class CategoryService:
    def __init__(self, db):
        self.db = db
    
    def list(self) -> List[Category]:
        query = self.db.execute("SELECT * from categories").fetchall()
        return [Category(id,title,ab,ae) for (id,title,ab,ae) in query]
    
    def get(self, id) -> Category | None:
        query = self.db.execute("SELECT * from categories where id=?", (id,)).fetchone()  
        if not query:
            return None
        id, title, ab, ae = query
        return Category(id,title,ab,ae)
    
    def rename(self, id: Category | int, new_title: str):
        if isinstance(id, Category):
            id = Category.id    
        self.db.execute("UPDATE categories SET title=? WHERE id=?", (id,new_title))
        
    #TODO 
    # 	#maybe for later, requires angle wrapping
	# delete(id) -> Bool
	# create(title, angle_begin, andle_end)
	# validate_ranges() #validates angles to remove/fix overlap and full 0-360°