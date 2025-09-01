from dataclasses import dataclass

@dataclass
class Category:
    """Category data class"""
    id: int
    title: str
    angle_begin: int 
    angle_end: int
    
    # def __init__(self, id: int, title: str, angle_begin: int , angle_end: int):
    #     self.id = id
    #     self.title = title
    #     self.angle_begin = angle_begin
    #     self.angle_end = angle_end
        
    # def __str__(self):
    #     return f"{self.id}, {self.title}, {self.angle_begin}, {self.angle_end}"

    # def __repr__(self):
    #     return f"{self.id}, {self.title}, {self.angle_begin}, {self.angle_end}"
    
    # def __eq__(self, value):
    #     if not isinstance(value, Category):
    #         return False
    #     return self.id == value.id
    
    # def __hash__(self):
    #     return hash(self.id)