class Category:
    """Category data class"""
    def __init__(self, id: int, title: str, angle_begin: int , angle_end: int):
        self.id = id
        self.title = title
        self.angle_begin = angle_begin
        self.angle_end = angle_end