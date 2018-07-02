# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:25:52 2018

@author: pedrobw
"""

import Print

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
    temp_nodes = []
    name = ["TypeLabel", "Node", "Label", "Type", "Pos", "Length"]
    
    def __init__(self, ttype, label, typeLabel, pos, length, children, char):
        self.type = ttype
        self.label = label
        self.typeLabel = typeLabel
        self.pos = pos
        self.length = length
        self.children = children
        self.char = char
        self.node = len(AST.nodes)
        AST.nodes.append(self)
        self.attributes = [self.typeLabel, self.node, self.label, self.type,
                           self.pos, self.length]
        
    def __str__(self):        
        s = "\t"
        for i in range(len(self.attributes)):
            if self.attributes[i] != None:
                s += AST.name[i] + "(" + str(self.attributes[i]) + ") "
        s += "Children(" + str(len(self.children)) + ")"
        return s
        
def get_lasts():
    t = ttype.pop()
    la = label.pop()
    tl = typeLabel.pop()
    p = pos.pop()
    le = length.pop()
    c = children.pop()
    #print(t, la, tl, p, le)
    return t, la , tl, p, le, c
    
def see_lasts():
    t = ttype[-1]
    la = label[-1]
    tl = typeLabel[-1]
    p = pos[-1]
    le = length[-1]
    c = children[-1]
    #print(t, la, tl, p, le)
    return t, la , tl, p, le, c
    
def attributes_append(tl):
    global ttype, label, typeLabel, pos, length, children
    ttype.append(None)
    label.append(None)
    typeLabel.append(None)
    pos.append(None)
    length.append(None)
    children.append([])
    
def rec_trans(index=0):
    
    global ttype, label, typeLabel, pos, length
    global char, line, ast
    
    index += 1
    char += "  "
    while index < len(ast):
        
        line = ast[index]
        
        if line == "\"root\": {":
            attributes_append(None)
            Print.conditional(char + "root: {")
            index = rec_trans(index)
            
        elif "{" in line:
            Print.conditional(char + "{")
            attributes_append(None)
            char += "  "
            
        elif "\"" in line:
            line = line.split("\": ")
            attribute = line[0].split("\"")[1]
            content = "\": ".join(line[1:])
            if len(content) > 2:
                content = content[1:-2]
            Print.conditional(char + attribute + ": " + content)
            if attribute=="type":
                ttype[-1] = content
            elif attribute=="label":
                label[-1] = content
            elif attribute=="typeLabel":
                typeLabel[-1] = content
            elif attribute=="pos":
                pos[-1] = content
            elif attribute=="length":
                length[-1] = content
            elif attribute=="children":
                if content != "[]":
                    while "]" not in content:
                        if index < len(ast):
                            index = rec_trans(index)
                        else:
                            break
                
        elif "}," in line:
            char = char[:-2]
            Print.conditional(char + "},")
            t, la , tl, p, le, c = get_lasts()
            this_ast = AST(t, la, tl, p, le, c, char)
            children[-1].append(this_ast)
            
        elif "}" in line:
            char = char[:-2]
            Print.conditional(char + "}")
            t, la , tl, p, le, c = get_lasts()
            this_ast = AST(t, la, tl, p, le, c, char)
            children[-1].append(this_ast)
        elif "]" in line:
            char = char[:-2]
            Print.conditional(char + "]")
        
        index += 1
        
    return index
    
    
def AST_from_file(file):
    
    global ast
    
    with open(file, 'r', errors='replace') as ast_file:
        ast = [i.strip() for i in ast_file.readlines()[:-1]]
        
    Print.conditional("{")
    rec_trans()
    out = [i for i in AST.nodes]
    Print.conditional("}")
    AST.nodes = []
    
    return out
    
def recursive_print(tree):
    for i in range(len(tree.attributes)):
        if tree.attributes[i] != None:
            print(tree.char + AST.name[i] + "(" + str(tree.attributes[i]) + ")")
    if len(tree.children) == 0:
        print(tree.char + "Children[]")
    else:
        print(tree.char + "Children[")
        L = len(tree.children)
        last = L-1
        for i in range(L):
            print(tree.char + "  {")
            recursive_print(tree.children[i])
            if i == last:
                print(tree.char + "  }")
            else:
                print(tree.char + "  },")
        print(tree.char + "]")
    
    
        
                
if __name__=="__main__":    
    l = AST_from_file("gumtree_parse_test")
    root = l[-1]
    recursive_print(root)
            