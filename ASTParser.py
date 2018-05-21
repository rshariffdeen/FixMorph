#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 17 15:23:41 2018

@author: pedrobw
"""
import sys
import os

def read(f):
    return f.readline()

def framaC(f, file, var, path):
    slice_name = path + file.split("/")[-1].split(".c")[0]
    slice_name += "-" + function_name + "-" + var + ".c"
    #print(slice_name)
    instr = "frama-c -main " + f + " -slice-value " + var + " " + file
    instr += " -then-on 'Slicing export' -print | sed -e '1,/* Generated /d'"
    instr += " > " + slice_name
    print(instr)
    print(" ")
    os.system(instr)

def gen_slices(function_name, file, lp, lv, path):
    for p in lp:
        framaC(function_name, file, p, path)
    for v in lv:
        framaC(function_name, file, v, path)


file_c = sys.argv[1]
path = sys.argv[2] # P_a/ or P_b/
file = path + "declarations.txt"
file_name = file_c.split("/")[-1].split(".c")[0]
line = "asd"
lp = list()
lv = list()
function_name = ""
valid_func = False
var_dict = dict()

with open(file, 'r') as f:
    while(line):
        line = read(f)
        if "-FunctionDecl" in line and "extern" not in line and "line" in line:
            valid_func = True
            gen_slices(function_name, file_c, lp, lv, path)
            function_name = line.strip().split(" '")[0].split(" ")[-1]
            lp = []
            lv = []
            print("Function: "+function_name)
        elif "ParmVarDecl" in line and valid_func:
            par_name = line.strip().split(" '")[0].split(" ")[-1]
            lp.append(par_name)
            print("|-Parameter: "+par_name)
        elif "VarDecl" in line and valid_func:
            var_name = line.strip().split(" '")[0].split(" ")[-1]
            lv.append(var_name)
            print("|--Local Variable: "+var_name)
        else:
            valid_func = False

gen_slices(function_name, file_c, lp, lv, path)