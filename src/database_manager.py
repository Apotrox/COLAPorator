import sqlite3
from typing import Dict, Iterable


class Manager:
    """Please run the database availability function first before continuing as there will be issues without. Due to custom schemas being possible, this is not done automatically.""" 
    
    
    def __init__(self): 
        db_path = "test.db"
        self.__con = sqlite3.connect(db_path)
        self.cur = self.__con.cursor()

    def ensure_database_availability(self, tables:Dict[str,Dict[str, str]] = None ):
        """
        Ensures database has all necessary tables and columns. \n
        Table entries are supposed to look like: {"table name": {"column name": "value type (like TEXT)", ..}, ...} \n
        Note that the value type will be assigned to the variable, so choose sensibly. These can also contain things like NOT NULL and PRIMARY KEY\n
        Possible datatypes are: NULL, INTEGER, REAL, TEXT, BLOB
        A default database scheme will be used alternatively.
        """
        table_exists = []
        if(tables==None):
            tables = {
                "topics": { "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
                            "title" : "TEXT UNIQUE",
                            "description": "TEXT"}, #no need to back-reference to category, one way lookup is fine
                "slices": { "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
                            "title": "TEXT UNIQUE", #categories will be managed with the slices themselves
                            "angle_begin": "INTEGER",
                            "angle_end": "INTEGER",
                            "topic_id": "INTEGER NOT NULL, FOREIGN KEY (topic_id) REFERENCES topics (ID)"},
                "guests": { "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
                            "name": "TEXT",
                            "date": "TEXT"}
            }

        #tries to create tables based on the dict above. if it already exists, that's fine
        for table, columns in tables.items():
            exists = False
            column_names= ""
            for column, type in columns.items():
                column_names += f"{column} {type},"
            column_names = column_names[:-1]  #removes the last comma
            try:
                self.cur.execute(f"CREATE TABLE {table}({column_names})") #create the table with necessary columns
            except sqlite3.OperationalError as s: #if the table already exists, no need to make the program crash
                if("already exists" in str(s)):
                    exists=True
                else:
                    raise s
            table_exists.append(exists)

        #notifying user if any table didn't exist beforehand
        if(False in table_exists):
            print("At least one table did not exist before initialization. Content or values will be missing and need to be corrected.")   
        #now it is safe to assume that all necessary tables and columns are there

    #here i want to define all functions myself, even though they just point at the builtin ones
    #this persues the goal of only this class handling the entirety of the database with no object access from other classes
    
    def commit_changes(self):
        """commits changes inside the class instead of accessing the connection from outside the class"""
        self.__con.commit()
    
    
    def execute(self, query:str) -> sqlite3.Cursor: #adding the return type just to clarify it's usage
        try:
            return self.cur.execute(query)
        except Exception as e:
            print(f"Query execution failed due to: {str(e)}") #no need to have the entire database manager crash just because a query didn't execute correctly
    
    def execute_many(self, query:str, data: Iterable) -> sqlite3.Cursor:
        try:
            return self.cur.executemany(query, data)
        except Exception as e:
            print(f"Query execution failed due to: {str(e)}")
        
    def fetch_one(self, object: sqlite3.Cursor):
        return object.fetchone()
    
    def fetch_many(self, object: sqlite3.Cursor, amount: int = None):
        return object.fetchmany(amount)
    
    def fetchall(self, object: sqlite3.Cursor):
        return object.fetchall()
        
    def __del__(self):
        self.__con.close()