# -*- coding: utf-8 -*-

import os
from Utils import err_exit, clean_ASTs
import Print

class Project:
    
    def __init__(self, path, name):
        if not (os.path.isdir(path)):
            err_exit(name + " is not an appropriate directory path.", path)
        self.path = path
        self.name = name
        self.funcs = dict()
        self.structs = dict()
        self.clean()
        
    
    def clean(self):
        # Remove *.crochetAST, *.AST and *.vec files from directory
        Print.blue("Cleaning " + self.name + "...")
        clean_ASTs(self.path)