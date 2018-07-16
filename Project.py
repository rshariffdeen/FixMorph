# -*- coding: utf-8 -*-

import os
from Utils import err_exit, clean_ASTs, exec_com
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
        try:
            c = "echo $PWD"
            crochet_path = exec_com(c)[0]
            if not (os.path.isfile(path + "/compile_commands.json")):
                self.bear_make(crochet_path)
            else:
                c = "cat " + path + "/compile_commands.json"
                if int(len(exec_com(c)[0])) <=2:
                    self.bear_make(crochet_path)
            c = "cd " + crochet_path
            exec_com(c)       
                
        except Exception as e:
            err_exit(e, "Failed at bear making project.")
            
        
    def bear_make(self, crochet_path):
        try:
            c = "cd " + self.path + "; make clean;" + \
                "bear make > " + crochet_path + "/output/compile_warnings;"
            exec_com(c)
        except Exception as e:
            err_exit(e, "Bear make failed. Configure first.")
        
    def clean(self):
        # Remove *.crochetAST, *.AST and *.vec files from directory
        Print.blue("Cleaning " + self.name + "...")
        clean_ASTs(self.path)