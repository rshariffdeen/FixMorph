#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 15 16:37:26 2018

@author: pedrobw
"""
import sys


class DistanceMatrix:
    
    
    def __init__(self, file1, file2):
        
        # Dictionnary with distances between files
        self.dist_dict = dict()
        
        # Gets a list of vector, one vector for each line (for each file)
        self.Pa = self.vectors_from_file(file1)
        self.Pc = self.vectors_from_file(file2)
        
        # Computes the distance matrix
        for i in range(len(self.Pa)):
            v1 = self.Pa[i]
            for j in range(len(self.Pc)):
                v2 = self.Pc[j]
                self.dist_dict[self.index(i,j)] = self.compute_dist(v1[1], v2[1])
                
        # Finds most probable copies
        self.bests = dict()
        for ind in range(len(self.Pa)):
            copyPc = [i for i in self.Pc]
            i = [self.dist(ind, j) for j in range(len(self.Pc))]
            copyi = [self.dist(ind, j) for j in range(len(self.Pc))]
            first = min(i)
            last = first
            bestlist = []
            while(i):
                currmin = min(copyi)
                pos = copyi.index(currmin)
                last = currmin
                el = copyPc[pos]
                copyPc.remove(copyPc[pos])
                #print(el[0])
                el1 = el[0].split("/")[-1]
                pos = copyi.index(currmin)
                if (last > 2*first and last > 25):
                    break
                bestlist.append((currmin, ind, el1))
                copyi.remove(currmin)
            index = self.Pa[ind][0]
            self.bests[index] = tuple(bestlist)
        
    
    def index(self, i,j):
        return str(i) + "|" + str(j)
        
    def get_Pa(self, i):
        return self.Pa[i]
    
    def get_Pc(self, j):
        return self.Pc[j]
        
    def get_distance(self, indexA, indexB):
        return self.dist_dict[self.index(indexA, indexB)]
    
    # Given a file with a path to a .vec file, it puts them in a list
    def vectors_from_file(self, file):
        l = list()
        with open(file, 'r') as f:
            a = f.readline().strip()
            while(a):
                v1 = self.get_vector_from_file(a)
                if v1:
                    l.append((a, v1))
                a = f.readline().strip()
        return l
            
    # For a .vec file, generates the corresponding vector as int list
    def get_vector_from_file(self, file1):
        with open(file1, 'r') as f1:
            a = f1.readline()
            #This condition is here because sometimes an empty file is generated
            if a:
                l = f1.readline().strip().split(" ")
                v1 = [int(x) for x in l]
                return v1

    # Euclidean distance between two vectors given as int lists
    def compute_dist(self, v1, v2):
        if v1 and v2:
            assert(len(v1)==len(v2))
            return sum((v1[i]-v2[i])**2 for i in range(len(v1)))
    
    # For two .vec files, computes the distance between the vectors (unused)
    def dist_from_files(self, file1, file2):
        v1 = self.get_vector_from_file(file1)
        v2 = self.get_vector_from_file(file2)
        return self.compute_distance(v1,v2)
        
    def dist(self, i, j):
        return self.dist_dict[self.index(i,j)]

    def __str__(self):
        output = "-"*120 + "\n"
        for i in range(len(self.Pa)):
            output += str(self.Pa[i][0]) + ":\n"
            for j in range(len(self.Pc)):
                output+= "\t" + str(self.dist(i,j)) + "\t" + self.Pc[j][0] + "\n"
            output += "-"*120 + "\n"
        output += "Closest function matches:\n"
        for key in self.bests.keys():
           output += "****\t" + str(key) + "\n"
           output += str(self.bests[key]) + "\n"
        return output



# Given two .txt files with paths to .vec files, computes the distance
# between each pair and prints the distance matrix.    
def matrix_distance_from_files(file1, file2):
    distMatrix = DistanceMatrix(file1, file2)
    return distMatrix
    
# Main program
# Asks for two .txt files with paths to .vec files and calls 
if __name__=="__main__":
    print(sys.argv[1], sys.argv[2])
    matrix_distance_from_files(sys.argv[1], sys.argv[2])