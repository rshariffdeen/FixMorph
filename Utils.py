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
    exit(-1)
    
''' Cleaning Residual files '''

def clean_ASTs(src_path):
    # Erase *.crochetAST, *.AST and *.vec files
    c = "find " + src_path + " -type f  \( -name \*.crochetAST" \
        + " -o -name \*.AST -o -name \*.vec \) -exec rm -f {} \;"
    exec_com(c, False)
    
    
def clean():
    # Remove other residual files stored in ./output/
    Print.blue("Removing other residual files...")
    if os.path.isdir("output"):
        r = "rm -rf 'output'; mkdir output;"
        exec_com(r, False)
        
    
''' Finding files with specific extension'''
    
def find_files(src_path, extension, output):
    # Save paths to all files in src_path with extension extension to output
    c = "find " + src_path + " -name '" + extension + "' > " + output
    exec_com(c, False)
    

''' Remove annoying hexadecimal numbers from some line.split(" ") '''

def remove_Hexa(linelist):
    for i in range(len(linelist)):
        # We remove hexadecimal numbers referring to memory
        if len(linelist[i]) >= 2:
            if ("0x" == linelist[i][0:2]):
                linelist[i] = ""
    # Back to a string, without annoying hexadecimal numbers
    line = " ".join(linelist)
    return line


''' Put irrelevant extensions and files in src_path line by line in output'''

def get_extensions(src_path, output):
    extensions = set()
    c = "find " + src_path + " -type f -not -name '*\.c' > " + output
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