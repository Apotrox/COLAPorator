import sqlite3
from typing import List
from .Topic import Topic
from categories.Category import Category
from database.database_manager import Manager

class TopicService:
    def __init__(self, db: Manager):
        self.db = db
    
    def list_all(self) -> List[Topic]:
        """Returns list of all topics sorted ASC by ID"""
        query = self.db.execute("SELECT * from topics").fetchall()
        return sorted([Topic(id, title, desc) for (id, title, desc) in query], key = lambda x: x.id)
    
    def list_by_category(self, category_id: int | Category) -> List[Topic]:
        """Returns list of all Topics of a specific category sorted ASC by ID"""
        if isinstance(category_id, Category):
            category_id = category_id.id
        
        query = self.db.execute("SELECT topics.id, topics.title, topics.description from topics \
                                INNER JOIN topicAssignment as TA on topics.id = ta.topic_id \
                                WHERE ta.category_id=?", (category_id,)).fetchall()
        return sorted([Topic(id, title, desc) for (id, title, desc) in query], key = lambda x: x.id)

    def get(self, topic_id: int) -> Topic | None:
        """Returns single topic based on integer ID provided"""
        query = self.db.execute("SELECT * from topics WHERE id=?", (topic_id,)).fetchone()
        id, title, desc = query
        return Topic(id, title,desc)
    
    def update(self, id: Topic | int, new_title: str | None = None, new_desc: str|None = None):
        """Updates Values for topics. If values are NoneType / have been left empty, the old value is used"""
        if isinstance(id, Topic):
            if not new_title:
                new_title=id.title
            if not new_desc:
                new_desc=id.description
            id=id.id
            
        if not new_title:
            new_title = self.get(id).title
        
        if not new_desc:
            new_desc = self.get(id).description
        # makes it a lot simpler than having to construct custom queries for each case 
        self.db.execute("UPDATE topics SET title=?, description=? WHERE id=?", (new_title, new_desc, id))
        self.db.commit_changes()

    def get_assignments(self, topic_id: int) -> List[int]:
        """Returns list of category IDs a single topic is assigned to"""
        query = self.db.execute("SELECT category_id from topicAssignment as TA where topic_id=?", (topic_id,)).fetchall()
        return [value for (value,) in query]
    
    def set_assignment(self, topic_id: int, category_ids: List[int]):
        """Overwrides all Category assignments of a topic"""
        self.db.execute("DELETE FROM topicAssignment WHERE topic_id=?", (topic_id,)) #just remove all entries related to the topic
        self.db.execute_many("INSERT INTO topicAssignment (topic_id, category_id) VALUES (?, ?)", [(topic_id, category_id) for category_id in category_ids])
        self.db.commit_changes()
            
    def add_topic(self):
        nt_amount = self.db.execute("SELECT id from topics where title LIKE 'New Topic'").fetchall()
        topic_name = f"New Topic {len(nt_amount) +1}"
        self.db.execute("INSERT INTO topics (title, description) VALUES (?, 'Placeholder Description')", (topic_name,))
        self.db.commit_changes()
    
    def remove_topic(self, topic_id: int | Topic):
        if isinstance(topic_id, Topic):
            topic_id=topic_id.id
        
        self.db.execute("DELETE FROM topics WHERE id=?", (topic_id,))
        self.db.commit_changes()