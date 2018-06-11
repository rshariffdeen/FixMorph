# -*- coding: utf-8 -*-
"""
Created on Tue Jun  5 16:14:29 2018

@author: pedrobw
"""

import subprocess as sub
import time
import sys

deckard_gen = "tools/Deckard/src/main/cvecgen"

def exec_com(command):
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()

    return p.returncode
    
def vec_gen(file_path):
    c = deckard_gen + " " + file_path
    return exec_com(c)

def vec_gen_prev(file_path):
    c = deckard_gen + "_fail " + file_path
    return exec_com(c)
    
def vec_compare(file_path):
    e1 = vec_gen(file_path)
    e2 = vec_gen_prev(file_path)
    if e1 != e2:
        if str(e1) == "65":
            print(file_path)
            print(e1)
            return 0
        elif str(e1) == "222":
            print(file_path)
            print(e1)
            return 0
        else:
            #print("success")
            return 1
    return 0
    
def find_files(src_path, extension, output):
    # Save paths to all files in src_path with extension extension to output
    c = "find " + src_path + " -name '" + extension + "' > " + output
    exec_com(c)
    
def comparerun():
    #p = "/home/pedrobw/Documents/Success/Openjpeg/"
    #find_files(p, "*.c", "Cfiles")
    with open('failed', 'r') as file:
        lines = [line.strip() for line in file.readlines()]
    count = 0
    for line in lines:
        count += vec_compare(line)
    print(count)
    
    
def testrun(p):
    find_files(p, "*.c", "Cfiles")
    with open("Cfiles", 'r') as file:
        lines = [line.strip() for line in file.readlines()]
    count = 0
    worst = 10
    lines_failed = []
    for line in lines:
        before = time.time()
        vec = str(vec_gen(line))
        dif = time.time() - before
        if dif > worst:
            worst = dif
            print(worst, line)
        if vec == "65" or vec == "222":
            print(line)
            lines_failed.append(line)
            count += 1
    print(count)
    with open('failed', 'w') as failed:
        failed.write("\n".join(lines_failed) + "\n")
            
def test_single(p):
    vec_gen(p)
    

if __name__ == "__main__":
    start = time.time()
    print("#"*120 + "\nStarting Test (Failing files)\n"+"#"*120)
    testrun(sys.argv[1])
    print("#"*120 + "\nStarting Compare (Those that weren't failing before)\n"+"#"*120)
    print("Time = " + str(time.time()-start))
    
    
