class Topic:
    def __init__(self, id:int , title: str, description: str):
        self.id = id
        self.title = title
        self.description = description
        
    
    def __str__(self):
        return f"{self.id}, {self.title}, {self.description}"

    def __repr__(self):
        return f"{self.id}, {self.title}, {self.description}"