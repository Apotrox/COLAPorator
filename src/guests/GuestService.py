from .Guest import Guest
from database.database_manager import Manager
from dataclasses import astuple
from datetime import datetime

class GuestService:
    def __init__(self, db:Manager):
        self.db = db
    
    def add_entry(self, guest:Guest):
        self.db.execute("INSERT INTO guests (name, institution,role,purpose_of_visit, date) VALUES (?,?,?,?,?)",(astuple(guest)+(datetime.now(),)))
        self.db.commit_changes()