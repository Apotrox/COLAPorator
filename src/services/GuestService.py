from data.Guest import Guest
from database.database_manager import Manager
from dataclasses import astuple
from datetime import datetime

from typing import List


class GuestService:
    def __init__(self, db:Manager):
        self.db = db
    
    def list(self) -> List[Guest]:
        query = self.db.execute("SELECT * FROM guests").fetchall()
        return sorted([Guest(id,name,inst,role,pov,date) for (id,name,inst,role,pov,date) in query], key=lambda x:x.id)
    
    def get_for_id(self, id: int) -> Guest|None:
        query = self.db.execute("SELECT * FROM guests WHERE id=?", (id,)).fetchone()
        if query:
            id,name,inst,role,pov,date = query
            return Guest(id,name,inst,role,pov,date)
        else:
            return None
    
    def add_entry(self, guest:Guest):
        """Adds an entry based on guest provided. Does not require ID, nor datetime, both of which will be handled here separately."""
        _,name,institution,role,pov,_ = guest
        self.db.execute("INSERT INTO guests (name, institution,role,purpose_of_visit, date) VALUES (?,?,?,?,?)",(name,institution,role,pov, datetime.now()))
        self.db.commit_changes()
        
    def delete_entry(self, guest_id: int | Guest):
        if isinstance(guest_id, Guest):
            guest_id = guest_id.id
        
        self.db.execute("DELETE FROM guests WHERE id=?",(guest_id,))
        self.db.commit_changes()