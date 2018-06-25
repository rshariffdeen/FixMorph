# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 16:17:47 2018

@author: pedrobw
"""

import os
from Utils import err_exit, clean_ASTs
import Print

class Project:
    
    def __init__(self, path, name):
        if not (os.path.isdir(path)):
            err_exit(name + " is not an appropriate directory path.")
        self.path = path
        self.name = name
        self.funcs = dict()
        self.structs = dict()
        self.clean()
        
    
    def clean(self):
        # Remove *.crochetAST, *.AST and *.vec files from directory
        Print.blue("Cleaning " + self.name + "...")
        clean_ASTs(self.path)