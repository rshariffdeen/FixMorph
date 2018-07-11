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
    attr_names = ['id', 'identifier', 'line', 'begin', 'end', 'value', 'type']
    
    def __init__(self, dict_ast, char=""):
        AST.nodes.append(self)
        self.id = None
        self.identifier = None
        self.line = None
        self.begin = None
        self.end = None
        self.value = None
        self.type = None
        self.char = char + "  "
        self.children = []
        if 'id' in dict_ast.keys():
            self.id = dict_ast['id']
        if 'identifier' in dict_ast.keys():
            self.identifier = dict_ast['identifier']
        if 'start line' in dict_ast.keys():
            self.line = dict_ast['start line']
        if 'begin' in dict_ast.keys():
            self.begin = dict_ast['begin']
        if 'end' in dict_ast.keys():
            self.end = dict_ast['end']
        if 'value' in dict_ast.keys():
            self.value = dict_ast['value']
        if 'type' in dict_ast.keys():
            self.type = dict_ast['type']
        if 'children' in dict_ast.keys():
            for i in dict_ast['children']:
                child = AST(i, char + "    ")
                self.children.append(child)
                child.parent = self
        
                    
    def treeString(self):
        self.attrs = [self.id, self.identifier, self.line, self.begin,
                      self.end, self.value, self.type]
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
        self.attrs = [self.id, self.identifier, self.line, self.begin,
                      self.end, self.value, self.type]
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
                            
        
def AST_from_file(file):
    
    global ast
    
    with open(file, 'r', errors='replace') as ast_file:
        ast = ast_file.readline()
    object_ast = json.loads(ast)
    ast = AST(object_ast['root'])
    return ast


            