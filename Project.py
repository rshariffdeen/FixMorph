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
            if not (os.path.isfile(path + "/compile_commands.json")):
                c = "AUX_PATH=$PWD"
                exec_com(c)
                c = "cd " + self.path + "; make clean; bear make; cd $AUX_PATH"
                exec_com(c)
            else:
                c = "cat " + path + "/compile_commands.json"
                if int(len(exec_com(c)[0])) <=2:
                    c = "AUX_PATH=$PWD"
                    exec_com(c)
                    c = "cd " + self.path + "; make clean;"
                    c += "bear make > output/compile_warnings; cd $AUX_PATH"
                    exec_com(c)
        except Exception as e:
            err_exit(e, "Failed at bear making project.")
            
        
        
    
    def clean(self):
        # Remove *.crochetAST, *.AST and *.vec files from directory
        Print.blue("Cleaning " + self.name + "...")
        clean_ASTs(self.path)