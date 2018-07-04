# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:30:48 2018

@author: pedrobw
"""

import time
import Project
import ASTgen
import ASTVector
import gumtreeASTparser
import Print

def test_ASTparsing():
    path = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/" + \
           "Backporting/Buffer_Overflow-Espruino/Pc/"
    project = Project.Project(path, "P")
    path_to_file = "targets/esp8266/esp8266_board_utils.c"
    file = path + path_to_file
    ASTgen.parseAST(file, project)
    
    
def test_gumtreeParsing1():
    for i in gumtreeASTparser.AST_from_file("gumtree_parse_test"):
        Print.white(i)
    
    
def test_gumtreeParsing2():
    l = gumtreeASTparser.AST_from_file("gumtree_parse_test")
    root = l[-1]
    gumtreeASTparser.recursive_print(root)
    
def test_gen_AST():
    src = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/" + \
          "Test/GraphicsMagick/Pc/"
    file = src + "hp2xx/old/to_pcx.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    file = src + "ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
def test_dist():
    file1 = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/Backporting/Buffer_Overflow-Jasper-2/Pa/src/libjasper/jpc/jpc_dec.c.jpc_dec_process_siz.vec"
    file2 = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/Backporting/Buffer_Overflow-Jasper-2/Pc/src/libjasper/jpc/jpc_dec.c.jpc_dec_process_siz.vec"
    file3 = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/Backporting/Buffer_Overflow-Jasper-2/Pc/src/libjasper/jpc/jpc_dec.c.jpc_dec_process_cod.vec"
    d12 = ASTVector.ASTVector.file_dist(file1, file2)
    d13 = ASTVector.ASTVector.file_dist(file1, file3)
    print(d12, d13, d12 < d13)
    
def run():
    Print.title("Running crochet tests...")
    tests = [test_ASTparsing,
             test_gumtreeParsing1,
             test_gumtreeParsing2,
             #test_gen_AST,
             test_dist]
    for i in tests:
        Print.green("-"*120)
        Print.rose("Starting test " + str(i.__name__) + "...")
        print("")
        start = time.time()
        i()
        end = time.time()
        secs = str(end - start)
        print("")
        Print.rose("Successful test after " + secs + " seconds.")
        print("")
    Print.green("-"*150)
    

if __name__=="__main__":
    run()