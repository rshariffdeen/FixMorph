# -*- coding: utf-8 -*-

import json

node = -1

ttype = [None]
label = [None]
typeLabel = ["Root"]
pos = [None]
length = [None]
children = [[]]
char = ""
line = ""
ast = []
index = 0


class AST:
    
    nodes = []
    attr_names = ['id', 'identifier', 'line', 'line_end', 'col', 'col_end',
                  'begin', 'end', 'value', 'type', 'file']
    
    def __init__(self, dict_ast, char=""):
        AST.nodes.append(self)
        self.id = None
        self.identifier = None
        self.line = None
        self.col = None
        self.begin = None
        self.end = None
        self.value = None
        self.type = None
        self.file = None
        self.char = char + "  "
        self.children = []
        if 'id' in dict_ast.keys():
            self.id = dict_ast['id']
        if 'identifier' in dict_ast.keys():
            self.identifier = dict_ast['identifier']
        if 'start line' in dict_ast.keys():
            self.line = dict_ast['start line']
        if 'end line' in dict_ast.keys():
            self.line_end = dict_ast['end line']
        if 'start column' in dict_ast.keys():
            self.col = dict_ast['start column']
        if 'end column' in dict_ast.keys():
            self.col_end = dict_ast['end column']
        if 'begin' in dict_ast.keys():
            self.begin = dict_ast['begin']
        if 'end' in dict_ast.keys():
            self.end = dict_ast['end']
        if 'value' in dict_ast.keys():
            self.value = dict_ast['value']
        if 'type' in dict_ast.keys():
            self.type = dict_ast['type']
        if 'file' in dict_ast.keys():
            self.file = dict_ast['file']
        if 'children' in dict_ast.keys():
            for i in dict_ast['children']:
                child = AST(i, char + "    ")
                self.children.append(child)
                child.parent = self
        
                    
    def treeString(self):
        self.attrs = [self.id, self.identifier, self.line, self.line_end,
                      self.col, self.col_end, self.begin, self.end, self.value,
                      self.type, self.file]
        s = self.char[:-2] + "{\n"
        for i in range(len(self.attrs)):
            if self.attrs[i] != None:
                s += self.char + self.attr_names[i] + ": "
                s += str(self.attrs[i]) + "\n"
        if len(self.children) > 0:
            s += self.char + "children [\n"
            for i in range(len(self.children)-1):
                s += str(self.children[i])
                s += ",\n"
            s += str(self.children[-1]) + "\n"
            s += self.char + "]\n"
        else:
            s += self.char + "children []\n"
        s += self.char[:-2] + "}"
        return s
        
    def __str__(self):
        self.attrs = [self.id, self.identifier, self.line, self.line_end,
                      self.col, self.col_end, self.begin, self.end, self.value,
                      self.type, self.file]
        s = ""
        for i in range(len(self.attrs)):
            if self.attrs[i] != None:
                s += AST.attr_names[i] + "(" + str(self.attrs[i]) + ") "
        s += "children["
        s += str(len(self.children))
        s += "]"
        return s
        
    def get_code(self, file):
        with open(file, 'r', errors='replace') as f:
            source_code = "".join(f.readlines())
        return source_code[int(self.begin):int(self.end)]
        
    def get_nodes(self, attribute, value, nodes):
        self.attrs = [self.id, self.identifier, self.line, self.line_end,
                      self.col, self.col_end, self.begin, self.end, self.value,
                      self.type, self.file]
        if attribute not in AST.attr_names:
            return 0
        index = AST.attr_names.index(attribute)
        if self.attrs[index] == value:
            nodes.append(self)
        for child in self.children:
            if child.get_nodes(attribute, value, nodes) == 0:
                return 0
        return 1
        
    # Note: I'm assuming contention is the only way of overlapping.
    def contains(self, other):
        if self.line < other.line and self.line_end >= other.line_end:
            return True
        elif self.line <= other.line and self.line_end > other.line_end:
            return True
        elif self.line == other.line and self.line_end == other.line_end:
            if self.col <= other.col and self.col_end >= other.col_end:
                return True
        return False
        
    def format_value(self, file):
        if "VarDecl" in self.type:
            nvalue = self.get_code(file)
        elif "(anonymous struct)::" in self.value:
            nvalue = self.get_code(file)
        else:
            nvalue = self.value
        return nvalue
       
       
    def info(self, file):
        if self.value:
            return node.type + ": " + self.format_value(file)
        return node.type
         
         
    def value_calc(self, file):
        if self.value:
            return self.format_value(file)
            
                            
        
def AST_from_file(file):
    
    global ast
    
    with open(file, 'r', errors='replace') as ast_file:
        ast = ast_file.readline()
    object_ast = json.loads(ast)
    AST(object_ast['root'])
    ast = [i for i in AST.nodes]
    AST.nodes = []
    return ast


            