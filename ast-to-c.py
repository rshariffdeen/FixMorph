from __future__ import print_function
import os, sys
from pycparser import c_generator
import pickle


def translate_to_c(ast_file_path):

    if os.path.isfile(ast_file_path):
        with open(ast_file_path, 'rb') as file:
            ast = pickle.load(file)
            generator = c_generator.CGenerator()
            print(generator.visit(ast))
    else:
        print ("Invalid file: file could not be opened")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        translate_to_c(sys.argv[1])
    else:
        print("Please provide a filename as argument")
