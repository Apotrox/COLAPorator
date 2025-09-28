from dataclasses import dataclass

@dataclass
class Guest:
    """Guest data class"""
    id: int | None #set to none to not bother with it on creation but enable the option for later 
    name:str
    institution:str
    role: str
    purpose_of_visit:str
    
    def __iter__(self):
        return iter((self.id, self.name, self.institution, self.role, self.purpose_of_visit))
    
    # def __init__(self, name:str, institution:str, role: str, purpose_of_visit:str):
    #     self.name = name
    #     self.inst = institution
    #     self.role = role
    #     self.pov = purpose_of_visit
    
    # def __str__(self):
    #     return "%s, %s, %s, %s" % (self.name, self.inst, self.role, self.pov)
    
    # def __repr__(self):
    #     return "(%s, %s, %s, %s)" % (self.name, self.inst, self.role, self.pov)
        