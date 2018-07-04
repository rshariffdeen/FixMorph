# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 08:54:05 2018

@author: pedrobw
"""

import Print
from Utils import exec_com, err_exit
import os

class ASTVector:
    
    deckard_path = "tools/Deckard/src/main/cvecgen_fail "
    deckard_path_2 = "tools/Deckard/src/main/cvecgen "
    deckard_vecs = dict()
    
    def __init__(self, proj, file, function, start, end, Deckard=True):
        self.proj = proj
        self.file = file
        self.function = function
        self.start = start
        self.end = end
        self.length = int(end) - int(start)
        self.variables = []
        self.params = []
        self.vector_path = self.file + "." + self.function + ".vec"
        self.vector = None
        if Deckard:
            self.vector = self.gen_Deckard_vec()
        if proj.name not in ASTVector.deckard_vecs.keys():
            ASTVector.deckard_vecs[proj.name] = list()
        ASTVector.deckard_vecs[proj.name].append(self.vector)
        
    def gen_Deckard_vec(self):
        current = "\t" + self.function + " " + str(self.start) + "-" + \
                    str(self.end)
        Print.grey(current, False)
        start = self.start
        end = self.end
        with open(self.file, 'r', errors='replace') as file:
            ls = file.readlines()
            max_line = len(ls)
            if int(end) > max_line:
                # TODO: This shouldn't happen!
                Print.red(current)
                err_exit("Deckard fail. The following file was not generated:",
                         self.vector_path)
                return None
            while start > 0:
                j = start-1
                if ";" in ls[j] or "}" in ls[j] or "#include" in ls[j]:
                    break
                start = j
        self.start = start
        self.end = end
        
        c = "echo " + self.vector_path + "\n >>  output/errors; "
        c += ASTVector.deckard_path + " --start-line-number " + \
            str(self.start) + " --end-line-number " + str(self.end) + " " + \
            self.file + " -o " + self.vector_path + " 2>> output/errors"
            
        try:
            exec_com(c, False)
        except Exception as e:
            err_exit(e, "Error with Deckard vector generation. Exiting...")
    
        if not os.path.isfile(self.vector_path):
            c1 = "echo " + self.vector_path + "\n >>  output/errors; "
            c1 += ASTVector.deckard_path_2 + " --start-line-number " + \
                 str(self.start) + " --end-line-number " + str(self.end) + \
                 " " + self.file + " -o " + self.vector_path + \
                 " 2>> output/errors"
            try:
                exec_com(c1, False)
            except Exception as e:
                err_exit(e, "Error with Deckard vector generation. Exiting...")
        
        if not os.path.isfile(self.vector_path):
            Print.yellow("Deckard fail. The vector file was not generated:")
            Print.yellow(self.vector_path)
            with open('output/reproduce_errors', 'a') as file:
                    file.write(c + "\n" + c1 + "\n")
            return None
            
        with open(self.vector_path, 'r') as vec_file:
            first = vec_file.readline()
            if first:
                v = [int(s) for s in vec_file.readline().strip().split(" ")]
                v = ASTVector.normed(v)
                return v
        
    
    def norm(v):
        return sum(v[i]**2 for i in range(len(v)))**(1/2)
        
    def normed(v):
        n = ASTVector.norm(v)
        return [i/n for i in v]
        
    def dist(u, v):
        assert(len(u)==len(v))
        return sum(((u[i] - v[i])**2) for i in range(len(u)))
        
    def file_dist(file1, file2):
        with open(file1, 'r', errors='replace') as f1:
            v = f1.readline()
            if v:
                v = [int(i) for i in f1.readline().strip().split(" ")]
                #v = ASTVector.normed(v)
                
        with open(file2, 'r', errors='replace') as f2:
            u = f2.readline()
            if v:
                u = [int(i) for i in f2.readline().strip().split(" ")]
                #u = ASTVector.normed(u)
        
        return ASTVector.dist(u, v)