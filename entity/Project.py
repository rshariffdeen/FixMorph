# -*- coding: utf-8 -*-

import os
from common.Utilities import err_exit, clean_ASTs, exec_com
from tools import Emitter


class Project:
    
    def __init__(self, path, name):
        if not (os.path.isdir(path)):
            err_exit(name + " is not an appropriate directory path.", path)
        if path[-1] != "/":
            path += "/"
        self.path = path
        self.name = name
        self.functions = dict()
        self.structs = dict()
        self.clean()
        try:
            if not (os.path.isfile(path + "/compile_commands.json")):
                self.make(bear=True)
            else:
                c = "cat " + path + "/compile_commands.json"
                if int(len(exec_com(c)[0])) <=2:
                    self.make(bear=True)      
                
        except Exception as e:
            err_exit(e, "Failed at bear making project. Check configuration.")
            
    def make(self, bear=False):
        c = "echo $PWD"
        crochet_path = exec_com(c)[0]
        c = "cd " + self.path + "; make clean;"
        if bear:
            c += "bear "
        c += "make > " + crochet_path + "/output/compile_warnings;"
        exec_com(c)
        c = "cd " + crochet_path
        exec_com(c)
        
    def clean(self):
        # Remove *.crochetAST, *.AST and *.vec files from directory
        Emitter.blue("Cleaning " + self.name + "...")
        clean_ASTs(self.path)