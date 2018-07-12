# -*- coding: utf-8 -*-

import os
import json
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
                #else:
                #    self.bear_make(crochet_path)
            with open(self.path + "/compile_commands.json", 'r', errors="replace") as file:
                text = "".join(file.readlines())[1:-1]
            text = "{\n\"a\":[\n" + text + "]}\n"
            dict_json = json.loads(text)["a"]
            for i in dict_json:
                if "arguments" in i.keys():
                    i["arguments"] = set(i["arguments"])
            aux_dict = []
            for i in dict_json:
                if len(aux_dict) == 0:
                    aux_dict.append(i)
                else:
                    file_i = i["file"]
                    dir_i = i["directory"]
                    nonexists = True
                    for j in aux_dict:
                        file_j = j["file"]
                        dir_j = j["directory"]
                        if file_i == file_j and dir_i == dir_j:
                            nonexists = False
                            j["arguments"] = j["arguments"].union(i["arguments"])
                    if nonexists:
                        aux_dict.append(i)
                        
            s = "[\n"
            count = 0
            L = len(aux_dict)
            for i in aux_dict:
                count += 1
                s += "    {\n"
                s += "        \"directory\": \"" + i["directory"] + "\",\n"
                s += "        \"file\": \"" + i["file"] + "\",\n"
                s += "        \"arguments\": [\n"
                many = 0
                l = len(i["arguments"])
                for value in i["arguments"]:
                    many += 1
                    s += "            \"" + value + "\""
                    if many < l:
                        s += ","
                    s += "\n"
                s += "        ]\n"
                s += "    }"
                if count  < L:
                    s += ","
                s += "\n"
            s += "]\n"
            #print(s)            
            with open(self.path + "/compile_commands.json", 'w') as file:
                file.write(s)
            c = "cd " + crochet_path
            exec_com(c)       
                
        except Exception as e:
            err_exit(e, "Failed at bear making project.")
            
        
    def bear_make(self, crochet_path):
        c = "cd " + self.path + "; make clean;" + \
            "bear make > " + crochet_path + "/output/compile_warnings;"
        exec_com(c)
        
    def clean(self):
        # Remove *.crochetAST, *.AST and *.vec files from directory
        Print.blue("Cleaning " + self.name + "...")
        clean_ASTs(self.path)