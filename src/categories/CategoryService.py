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
    
    def get(self, id:int) -> Category | None:
        query = self.db.execute("SELECT * from categories where id=?", (id,)).fetchone()  
        if not query:
            return None
        id, title, ab, ae = query
        return Category(id,title,ab,ae)
    
    def rename(self, id: Category | int, new_title: str):
        if isinstance(id, Category):
            id = Category.id    
        self.db.execute("UPDATE categories SET title=? WHERE id=?", (id,new_title))
        self.db.commit_changes()
        
    def get_for_angle(self, angle:int) -> Category | None:
        query = self.db.execute("SELECT * FROM categories WHERE (angle_begin <= angle_end AND ? BETWEEN angle_begin AND angle_end) \
            OR (angle_begin > angle_end AND (? >= angle_begin OR ? <= angle_end))", (angle,angle,angle)).fetchone()
            #angle wrapping
        if not query:
            return None
        id, title, ab, ae = query
        if query and all(query): #if there is actually data
            return Category(id,title,ab,ae)
        
        #return none in any other case
        return None
    
    def get_similar(self, name:str) -> List[Category] | None:
        """Returns list of Categories with a *similar* title"""
        query = self.db.execute("SELECT * FROM categories WHERE title LIKE ?", (name,)).fetchall()
        if query and all(query):
            return [Category(id, title,ab,ae) for (id,title,ab,ae) in query]
        
        return None
    
    def get_for_title(self, title:str) -> Category | None:
        """Returns Category with given name if exists"""
        query = self.db.execute("SELECT * FROM categories WHERE title=?", (title,)).fetchone()
        
        if query and all(query):
            id, title,ab,ae = query
            return Category(id, title, ab, ae)
        
        return None    
    
    def assign_angle(self, category:Category, angle_begin:int, angle_end:int, handle_overflow:bool=True):
        """Assigns new angles to an existing category. Will ONLY adjust other categories angles' accordingly if handle_overflow is set! handle_overflow True by default"""
        
        #angle wrapping
        angle_begin=angle_begin%360
        angle_end=angle_end%360
        
        
        if not handle_overflow:
            self.db.execute("UPDATE categories SET angle_begin=?, angle_end=? WHERE id=?", (angle_begin,angle_end,category.id))
            self.db.commit_changes()
            return
        
        #checking if end and begin are in range of another category
        next_category = self.get_for_angle(angle_end)
        previous_category = self.get_for_angle(angle_begin)
        
        if(next_category):
            self.assign_angle(next_category,angle_end, next_category.angle_end,False)
        if(previous_category):
            self.assign_angle(previous_category,previous_category.angle_begin, angle_end,False)
        
        self.assign_angle(category, angle_begin, angle_end, False)
    
    def create_category(self, title:str, angle_begin:int, angle_end:int, handle_overflow:bool=True):
        """Creates a new category based on data provided. Handles overflow by default.
        If the name is the same as another existing category, the angles will just be updated."""
        
        check_for_unique=self.db.execute("SELECT * from categories WHERE title=?",(title,)).fetchone()
        if check_for_unique:
            print("Same name category found, updating angles")
            id,title,ab,ae = check_for_unique
            self.assign_angle(Category(id,title,ab,ae), angle_begin, angle_end, True)
            return
        
        print("No same category found, creating new one")
        self.db.execute("INSERT INTO categories (title, angle_begin, angle_end) VALUES (?, ?, ?)", (title,0,0))
        self.db.commit_changes()
        
        #getting the ID of the new topic
        new_category = self.db.execute("SELECT * FROM categories WHERE title=? AND angle_begin=0 AND angle_end=0", (title,)).fetchone()
        id=new_category[0]
        
        self.assign_angle(Category(id,title,0,0), angle_begin, angle_end, True)
    
    def delete_category(self, category:Category, leave_empty:bool=False):
        """Deletes a given category from the Database. By default, the hole created will be closed by the categories surrounding it."""
        
        if not category:
            print(f"No category provided: {category}")
            return
        
        self.db.execute("DELETE FROM categories WHERE id=?", (category.id,))
        self.db.commit_changes()
        
        if not leave_empty:
            
            distance=abs(category.angle_end-category.angle_begin)/2
            
            next_category=self.db.execute("SELECT * FROM categories WHERE angle_begin>=?",(category.angle_end,)).fetchone()
            prev_category=self.db.execute("SELECT * FROM categories WHERE angle_end<=?",(category.angle_begin,)).fetchone()
            
            #just to get the Category object bc i'm too lazy to make it myself thanks
            next_category=self.get(next_category[0])
            prev_category=self.get(prev_category[0])

            self.assign_angle(next_category,(next_category.angle_begin-distance), next_category.angle_end, False)
            self.assign_angle(prev_category,prev_category.angle_begin,(prev_category.angle_end+distance),False)