class Position(object):
    def __init__(self, index: int, line: int, column: int, file: str, text: str):
        self.index = index
        self.line = line
        self.column = column
        self.file = file
        self.text = text
    
    def advance(self, current_char: str = None):
        self.index += 1
        self.column += 1
        
        if current_char == '\n':
            self.column = 0
            self.line += 1
    
    def copy(self):
        return Position(self.index, self.line, self.column, self.file, self.text)
