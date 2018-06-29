# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:25:52 2018

@author: pedrobw
"""

printer = False

node = -1

ttype = []
label = []
typeLabel = []
pos = []
length = []


class AST:
    
    nodes = []
    temp_nodes = []
    
    def __init__(self, ttype, label, typeLabel, pos, length, char):
        self.type = ttype
        self.label = label
        self.typeLabel = typeLabel
        self.pos = pos
        self.length = length
        self.char = char
        self.node = len(AST.nodes)
        if printer:
            print(self)
        AST.nodes.append(self)
        
    def __str__(self):
        l = [self.typeLabel, self.node, self.label, self.type, self.pos,
             self.length]
        name = ["\tTypeLabel(", "Node(", "Label(", "Type(", "Pos(", "Length("]
        name2 = [") ", ") ", ") ", ") ", ") ", ") "]
        s = ""
        for i in range(len(l)):
            if l[i] != None:
                s += name[i] + str(l[i]) + name2[i]
        return s
        
def get_lasts():
    t = ttype.pop()
    la = label.pop()
    tl = typeLabel.pop()
    p = pos.pop()
    le = length.pop()
    #print(t, la, tl, p, le)
    return t, la , tl, p, le
    
def see_lasts():
    t = ttype[-1]
    la = label[-1]
    tl = typeLabel[-1]
    p = pos[-1]
    le = length[-1]
    #print(t, la, tl, p, le)
    return t, la , tl, p, le
    
def rec_trans(ast, index, char, line):
    global ttype, label, typeLabel, pos, length
    if index == 0:
        if printer:
            print("{")
        ttype.append(None)
        label.append(None)
        typeLabel.append("Root")
        pos.append(None)
        length.append(None)
    index += 1
    while index < len(ast):
        line = ast[index]
        if line == "\"root\": {":
            char += "  "
            ttype.append(None)
            label.append(None)
            typeLabel.append("Root")
            pos.append(None)
            length.append(None)
            if printer:
                print(char + "root: {")
            a = rec_trans(ast, index, char + "  ", line)
            index, char, line = a
        elif "{" in line:
            if printer:
                print(char + "{")
            ttype.append(None)
            label.append(None)
            typeLabel.append(None)
            pos.append(None)
            length.append(None)
            char += "  "
        elif "\"" in line:
            line = line.split("\": ")
            attribute = line[0].split("\"")[1]
            content = "\": ".join(line[1:])
            if len(content) > 2:
                content = content[1:-2]
            if attribute=="type":
                ttype[-1] = content
                if printer:
                    print(char + "type:", content)
            elif attribute=="label":
                label[-1] = content
                if printer:
                    print(char + "label:", content)
            elif attribute=="typeLabel":
                typeLabel[-1] = content
                if printer:
                    print(char + "typeLabel:", content)
            elif attribute=="pos":
                pos[-1] = content
                if printer:
                    print(char + "pos:", content)
            elif attribute=="length":
                length[-1] = content
                if printer:
                    print(char + "length:", content)
            elif attribute=="children":
                if content == "[]":
                    if printer:
                        print(char + "children []")
                else:
                    if printer:
                        print(char + "children [")
                    while "]" not in content:
                        if index < len(ast):
                            a = rec_trans(ast, index, char+"  ", line)
                            
                            index, char, line = a
                        else:
                            break
                
                
                
        elif "}," in line:
            char = char[:-2]
            if printer:
                print(char + "},")
            t, la , tl, p, le = get_lasts()
            
            AST(t, la, tl, p, le, char) 
        elif "}" in line:
            char = char[:-2]
            if printer:
                print(char + "}")
            t, la , tl, p, le = get_lasts()
            AST(t, la, tl, p, le, char) 
        elif "]" in line:
            char = char[:-2]
            if printer:
                print(char + "]")
        
        index += 1
        
    
    return index, char, line
    
    
def AST_from_file(file, debug=False):
    global printer
    with open(file, 'r', errors='replace') as ast_file:
        ast = [i.strip() for i in ast_file.readlines()]

    rec_trans(ast, 0, "", "")
    out = [i for i in AST.nodes]
    AST.nodes = []
    return out
    
    
        
                
if __name__=="__main__":    
    for i in AST_from_file("gumtree_parse_test"):
        print(i)
            