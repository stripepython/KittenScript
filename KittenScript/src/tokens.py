from typing import Any, Optional

from .lexer.position import Position


class Token(object):
    def __init__(self, type_: str, value: Any = None, pos_start: Optional[Position] = None,
                 pos_end: Optional[Position] = None):
        self.type = type_
        self.value = value
        
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance(self.value)
        
        if pos_end:
            self.pos_end = pos_end.copy()
    
    def __repr__(self):
        if self.value:
            return f'{self.type}: {self.value}'
        return self.type
    
    def matches(self, type_: str, value: Any):
        return self.type == type_ and self.value == value
    
    def as_json(self):
        return {'type': self.type, 'value': self.value}
