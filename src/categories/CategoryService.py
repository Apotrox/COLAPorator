import sqlite3
from typing import List
from .Category import Category
from database.database_manager import Manager #just adding this for pylance purposes to make debugging a tiny bit easier

class CategoryService:
    def __init__(self, db: Manager):
        self.db = db
    
    def list(self) -> List[Category]:
        """Returns list of all categories. Sorted ASC by ID"""
        query = self.db.execute("SELECT * from categories").fetchall()
        return sorted([Category(id,title,ab,ae) for (id,title,ab,ae) in query], key=lambda x:x.id)
    
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
        
    def get_for_angle(self, angle:int) -> Category | None:
        query = self.db.execute("SELECT * FROM categories WHERE (angle_begin <= angle_end AND ? BETWEEN angle_begin AND angle_end) \
            OR (angle_begin > angle_end AND (? >= angle_begin OR ? <= angle_end))", (angle,angle,angle)).fetchone()
            #angle wrapping
        id, title, ab, ae = query
        if query and all(query): #if there is actually data
            return Category(id,title,ab,ae)
        else:
            return None
        
    #TODO 
    # 	#maybe for later, requires angle wrapping
	# delete(id) -> Bool
	# create(title, angle_begin, andle_end)
	# validate_ranges() #validates angles to remove/fix overlap and full 0-360°