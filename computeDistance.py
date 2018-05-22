#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 15 16:37:26 2018

@author: pedrobw
"""
import sys

# For a .vec file, generates the corresponding vector as int list
def get_vector_from_file(file1):
    with open(file1, 'r') as f1:
        a = f1.readline()
        #This condition is here because sometimes an empty file is generated
        if a:
            l = f1.readline().strip().split(" ")
            v1 = [int(x) for x in l]
            return v1

# Euclidean distance between two vectors given as int lists
def compute_distance(v1, v2):
    if v1 and v2:
        assert(len(v1)==len(v2))
        return sum((v1[i]-v2[i])**2 for i in range(len(v1)))

# For two .vec files, computes the distance between the vectors (unused)
def dist_from_files(file1, file2):
    v1 = get_vector_from_file(file1)
    v2 = get_vector_from_file(file2)
    return compute_distance(v1,v2)

# Given a .txt file with a path to a .vec file, it puts them in a list
def vectors_from_file(file):
    l = list()
    with open(file, 'r') as f:
        a = f.readline().strip()
        while(a):
            v1 = get_vector_from_file(a)
            if v1:
                l.append((a, v1))
            a = f.readline().strip()
    return l

# Given two .txt files with paths to .vec files, computes the distance
# between each pair and prints the distance matrix.    
def matrix_distance_from_files(file1, file2):
    l1 = vectors_from_file(file1)
    Matrix = []
    l2 = vectors_from_file(file2)
    for v1 in l1:
        row = []
        for v2 in l2:
            row.append(compute_distance(v1[1],v2[1]))
        Matrix.append(row)
    print("Rows:")
    for i in range(len(l1)):
        print("i="+str(i)+": "+l1[i][0])
    print("Columns:")
    for j in range(len(l2)):
        print("j="+str(j)+": "+l2[j][0])
    for i in Matrix:
        print(i)
    # Find most probable copies
    copyMatrix = [[j for j in i] for i in Matrix]
    for ind in range(len(copyMatrix)):
        copyl2 = [i for i in l2]
        i = copyMatrix[ind]
        copyi = [j for j in i]
        el0 = l1[ind][0].split("/")[-1]
        print("****\t", el0)
        first = min(i)
        last = first
        while(i != []):
            currmin = min(copyi)
            pos = copyi.index(currmin)
            last = currmin
            el = copyl2[pos]
            copyl2.remove(copyl2[pos])
            #print(el[0])
            el1 = el[0].split("/")[-1]
            pos = copyi.index(currmin)
            if (last > 2*first and last > 25):
                break
            print(str(currmin)+"\t", el1)
            #print(currmin)
            copyi.remove(currmin)
        print("--------------------")
    return Matrix
    
# Main program
# Asks for two .txt files with paths to .vec files and calls 
if __name__=="__main__":
    print(sys.argv[1], sys.argv[2])
    matrix_distance_from_files(sys.argv[1], sys.argv[2])