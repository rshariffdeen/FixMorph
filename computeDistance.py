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
        
        # List of files
        with open(file1, 'r') as f:
            self.f1 = [i.strip() for i in f.readlines()]
            
        with open(file2, 'r') as f:
            self.f2 = [i.strip() for i in f.readlines()]
    
        #print(self.f1, self.f2)
        
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
            first = min(i)
            last = first
            bestlist = []
            while(i):
                # currmin stores the best unexplored available match
                currmin = min(i)
                pos = i.index(currmin)
                last = currmin
                el = copyPc[pos][0]
                copyPc.remove(copyPc[pos])
                pos = i.index(currmin)
                # If the last scores doubles the best, we just stop searching
                if (last > 2*first and last > 25):
                    break
                bestlist.append((currmin, ind, el))
                i.remove(currmin)
            index = self.Pa[ind][0]
            self.bests[index] = tuple(bestlist)
        
    
    def index(self, i,j):
        return str(i) + "|" + str(j)
        
    def get_Pa(self, i):
        return self.Pa[i]
    
    def get_Pc(self, j):
        return self.Pc[j]
        
    def get_dist(self, indexA, indexB):
        return self.dist_dict[self.index(indexA, indexB)]
        
    def get_distance_files(self, fileA, fileB):
        return self.get_dist(self.f1.index(fileA), self.f2.index(fileB))
    
    # Given a file with paths to .vec files, it puts them as vectors in a list
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
            # This condition is here since sometimes an empty file is generated
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
    def compute_distance_files(self, file1, file2):
        v1 = self.get_vector_from_file(file1)
        v2 = self.get_vector_from_file(file2)
        return self.compute_distance(v1,v2)
        
    def dist(self, i, j):
        return self.dist_dict[self.index(i,j)]

    def vars_vec_file_f_path(self, vec):
        lfile = vec.split(".")
        file = lfile[-5].split("/")[-1] + ".c"
        function = lfile[-3]
        lines = lfile[-2]
        path = "/".join(vec.split("/")[:-1]) + "/"
        return file, function, lines, path
        
    def vars_vec_file_f_var_path(self, vec):
        lfile = vec.split(".")
        file = lfile[-6].split("/")[-1] + ".c"
        function = lfile[-4]
        var = lfile[-3]
        lines = lfile[-2]
        path = "/".join(vec.split("/")[:-1]) + "/"
        return file, function, lines, var, path
        
    def out_format(self, dist, file, f, lines, path, ind):
        out = dist + "\tFile: " + file + "\tLines: " + lines + "\tFunction: "
        out +=  f + "\tPath: " + path + "\tIndex: " + ind + "\n"
        return out
        
        
    def __str__(self):
        # For each file of Pa, we print the distance to each file of Pc
        out = "-"*150 + "\n"
        for i in range(len(self.Pa)):
            out += str(self.Pa[i][0]) + ":\n"
            for j in range(len(self.Pc)):
                out+= "\t" + str(self.dist(i,j)) + "\t" + self.Pc[j][0] + "\n"
            out += "-"*150 + "\n"
        # We also print the most probable clone functions
        out += "#"*150 + "\n"
        out += "Closest function matches:\n"
        out += "-"*150 + "\n"
        for key in self.bests.keys():
            ind = "i=" + str(self.f1.index(key))
            file, function, lines, path = self.vars_vec_file_f_path(key)
            out += self.out_format("******", file, function, lines, path, ind)
            for i in self.bests[key]:
                dist = str(i[0])
                ind = "j=" + str(i[1])
                i = i[2]
                file, function, lines, path = self.vars_vec_file_f_path(i)
                out += self.out_format(dist, file, function, lines, path, ind)
            out += "-"*150 + "\n"
        print (out)
        return out

    
# Main program: asks for two .txt files with paths to .vec files and calls 
if __name__=="__main__":
    if len(sys.argv) < 3:
        print("Insufficient arguments")
        exit(-1)
    print(sys.argv[1], sys.argv[2])
    print(DistanceMatrix((sys.argv[1], sys.argv[2])))
    #print(DistanceMatrix.bests)