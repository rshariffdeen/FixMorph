# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:30:48 2018

@author: pedrobw
"""

import time
import Project
import ASTcrochet
import gumtreeASTparser
import Print

def test_ASTparsing():
    Print.rose("Starting test for AST parsing...")
    print("")
    start = time.time()
    path = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/" + \
           "Backporting/Buffer_Overflow-Espruino/Pc/"
    project = Project.Project(path, "P")
    path_to_file = "targets/esp8266/esp8266_board_utils.c"
    file = path + path_to_file
    ASTcrochet.parseAST(file, project)
    end = time.time()
    secs = str(end - start)
    print("")
    Print.rose("Successful test after " + secs + " seconds.")
    print("")
    
    
def test_gumtreeParsing():
    Print.rose("Starting test for gumtree parsing...")
    print("")
    start = time.time()
    for i in gumtreeASTparser.AST_from_file("gumtree_parse_test"):
        Print.grey(i, False)
    end = time.time()
    secs = str(end - start)
    print("")
    Print.rose("Successful test after " + secs + " seconds.")
    print("")
        

def run():
    Print.title("Running crochet tests...")
    tests = [test_ASTparsing, test_gumtreeParsing]
    for i in tests:
        Print.green("-"*150)
        Print.rose(i.__name__)
        i()
    Print.green("-"*150)
    

if __name__=="__main__":
    run()