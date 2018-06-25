# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 08:54:05 2018

@author: pedrobw
"""

import Print
from Utils import exec_com, err_exit

class ASTVector:
    
    deckard_path = "tools/Deckard/src/main/cvecgen_fail "
    
    def __init__(self, file, function, start, end, Deckard=True):
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
        
    def gen_Deckard_vec(self):
        Print.grey("\t" + self.function + " " + str(self.start) + "-" +
                    str(self.end), False)
        c = ASTVector.deckard_path + " --start-line-number " + \
            str(self.start) + " --end-line-number " + str(self.end) + " " + \
            self.file + " -o " + self.vector_path + " 2>> output/errors"
        try:
            exec_com(c, False)
        except Exception as e:
            err_exit(e, "Error with Deckard vector generation. Exiting...")
    
        with open(self.vector_path, 'r') as vec_file:
            first = vec_file.readline()
            if first:
                v = [int(s) for s in vec_file.readline().strip().split(" ")]
                v = ASTVector.normed(v)
                return v
        return None
    
    def norm(v):
        return sum(v[i]**2 for i in range(len(v)))**(1/2)
        
    def normed(v):
        n = ASTVector.norm(v)
        return [i/n for i in v]
        
    def dist(u, v):
        assert(len(u)==len(v))
        return sum(((u[i] - v[i])**2) for i in range(len(u)))