# -*- coding: utf-8 -*-

import os
import subprocess
import Print


''' Executing commands '''

def exec_com(c, verbose=True):
    # Print executed command and execute it in console
    if verbose:    
        Print.grey(c)
    proc = subprocess.Popen([c], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # out is the output of the command, and err is the exit value
    return (out.decode("utf-8").strip(), err)
    

''' Error management '''

def err_exit(*args):
    print("\n")
    for i in args:
        Print.red(i)
    raise Exception("Error. Exiting...")
    
''' Cleaning Residual files '''

def clean_ASTs(src_path):
    # Erase *.crochetAST, *.AST and *.vec files
    c = "find " + src_path + " -type f  \( -name '*.crochetAST'" + \
        " -o -name '*.AST' -o -name '*.vec' -o -name '*.ASTalt' \) " + \
        "-exec rm -f {} \;"
    exec_com(c, False)
    
    
def clean():
    # Remove other residual files stored in ./output/
    Print.blue("Removing other residual files...")
    if os.path.isdir("output"):
        r = "rm -rf output Backup_Folder; mkdir output Backup_Folder;"
        exec_com(r, False)
        
    
''' Finding files with specific extension'''
    
def find_files(src_path, extension, output):
    # Save paths to all files in src_path with extension extension to output
    c = "find " + src_path + " -name '" + extension + "' > " + output
    exec_com(c, False)


''' Put irrelevant extensions and files in src_path line by line in output'''

def get_extensions(src_path, output):
    extensions = set()
    c = "find " + src_path + " -type f -not -name '*\.c' -not -name '*\.h'" + \
        " > " + output
    exec_com(c, False)
    with open(output, 'r') as f:
        a = f.readline().strip()
        while(a):
            a = a.split("/")[-1]
            if "." in a:
                extensions.add("*." + a.split(".")[-1])
            else:
                extensions.add(a)
            a = f.readline().strip()
    return extensions