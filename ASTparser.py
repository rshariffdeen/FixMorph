# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:25:52 2018

@author: pedrobw
"""

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
    attr_names = ['id', 'identifier', 'begin', 'end', 'value', 'type']
    
    def __init__(self, dict_ast, char=""):
        AST.nodes.append(self)
        self.id = None
        self.identifier = None
        self.begin = None
        self.end = None
        self.value = None
        self.type = None
        self.char = char + "  "
        self.children = []
        self.attributes = [self.id, self.identifier, self.begin, self.end,
                           self.value, self.type]
        for i in range(len(self.attr_names)):
            key = AST.attr_names[i]
            if key in dict_ast.keys():
                self.attributes[i] = dict_ast[key]
        if "children" in dict_ast.keys():
            for i in dict_ast['children']:
                    self.children.append(AST(i, char + "    "))
        
                    
    def __str__(self):
        s = self.char[:-2] + "{\n"
        for i in range(len(self.attributes)):
            if self.attributes[i] != None:
                s += self.char + self.attr_names[i] + ": "
                s += str(self.attributes[i]) + "\n"
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
        
        
def AST_from_file(file):
    
    global ast
    
    with open(file, 'r', errors='replace') as ast_file:
        ast = ast_file.readline()
    object_ast = json.loads(ast)
    ast = AST(object_ast['root'])
    return ast


            