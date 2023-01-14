class SymbolTable(object):
    
    class _NotFound(object):
        def __repr__(self):
            return 'NOTFOUND'
        
        def get(self):
            return self
    
    not_found = _NotFound()
    
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        
    def get(self, name):
        value = self.symbols.get(name, self.not_found)
        if value == self.not_found:
            if self.parent:
                value = self.parent.get(name)
        return value
    
    def set(self, name, value):
        self.symbols[name] = value
        
    def remove(self, name):
        if name not in self.symbols:
            return self.not_found
        del self.symbols[name]
        
    def update(self, dictionary: dict):
        self.symbols.update(dictionary)
        
    def copy(self):
        table = SymbolTable()
        table.symbols = self.symbols.copy()
        if self.parent:
            table.parent = self.parent.copy()
        return table
