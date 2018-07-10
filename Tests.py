# -*- coding: utf-8 -*-

import time
import Project
import ASTgen
import ASTVector
import ASTparser
import ASTdiffTest
import Print
from Utils import exec_com

examples_path = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/"

def test_ASTparsing():
    path = examples_path + "Backporting/Buffer_Overflow-Espruino/Pc/"
    project = Project.Project(path, "P")
    path_to_file = "targets/esp8266/esp8266_board_utils.c"
    file = path + path_to_file
    ASTgen.parseAST(file, project)
    
def test_ASTparsing1():
    src = examples_path + "Backporting/Null_Pointer_Dereference-Binutils/Pc/"
    project = Project.Project(src, "P")
    file = src + "bfd/pc532-mach.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.parseAST(file, project)
    
    
def test_treeParsing1():
    for i in ASTparser.AST_from_file("gumtree_parse_test"):
        Print.white(i)
    
    
def test_treeParsing2():
    l = ASTparser.AST_from_file("gumtree_parse_test")
    root = l[-1]
    ASTparser.recursive_print(root)
    
def test_gen_AST():
    src = examples_path + "Backporting/Invalid_Memory_Read-GraphicsMagick/Pc/"
    file = src + "hp2xx/old/to_pcx.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    file = src + "ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    
def test_gen_AST1():
    src = examples_path + "Backporting/Null_Pointer_Dereference-Binutils/Pc/"
    file = src + "bfd/pc532-mach.c" #"ralcgm/src/cgmotpz.c"
    ASTgen.gen_AST(file, src)
    
    
def test_dist():
    file1 = examples_path + "Backporting/Buffer_Overflow-Jasper-2/Pa/" + \
            "src/libjasper/jpc/jpc_dec.c.jpc_dec_process_siz.vec"
    file2 = examples_path + "Backporting/Buffer_Overflow-Jasper-2/Pc/" + \
            "src/libjasper/jpc/jpc_dec.c.jpc_dec_process_siz.vec"
    file3 = examples_path + "Backporting/Buffer_Overflow-Jasper-2/Pc/" + \
            "src/libjasper/jpc/jpc_dec.c.jpc_dec_process_cod.vec"
    
    Print.white("Absolute distance:")    
    d12 = ASTVector.ASTVector.file_dist(file1, file2)
    d13 = ASTVector.ASTVector.file_dist(file1, file3)
    Print.white(str(d12) + " < " + str(d13) + " ? " + str(d12 < d13))
    d12 = ASTVector.ASTVector.file_dist(file1, file2, normed=False)
    d13 = ASTVector.ASTVector.file_dist(file1, file3, normed=False)
    Print.white("Relative distance:")
    Print.white(str(d12) + " < " + str(d13) + " ? " + str(d12 < d13))
    

def test_ASTdump():
    file1 = examples_path + "Backporting/Buffer_Overflow-Libarchive/Pa/libarchive/archive_read_support_format_ar.c"
    c = "tools/bin/crochet-diff -ast-dump-json " + file1 + " > " + \
        "output/test_AST 2> /dev/null"
    exec_com(c)
    #ast = ASTparser.AST_from_file("output/test_AST")
    #print(ast.treeString())
    
    ast = ASTdiffTest.AST_from_file("output/test_AST")
    with open("output/test1", 'w') as f1:
        f1.write(ast.treeString())
        
    file2 = examples_path + "Backporting/Buffer_Overflow-Libarchive/Pb/libarchive/archive_read_support_format_ar.c"
    c = "tools/bin/crochet-diff -ast-dump-json " + file2 + " > " + \
        "output/test_AST 2> /dev/null"
    exec_com(c)
    #ast = ASTparser.AST_from_file("output/test_AST")
    #print(ast.treeString())
    
    ast = ASTdiffTest.AST_from_file("output/test_AST")
    with open("output/test2", 'w') as f2:
        f2.write(ast.treeString())
    
    
def run():
    Print.title("Running crochet tests...")
    tests = [
             #test_ASTparsing,
             #test_ASTparsing1,
             #test_treeParsing1,
             #test_treeParsing2,
             #test_gen_AST,
             #test_gen_AST1,
             #test_dist,
             test_ASTdump
             ]
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