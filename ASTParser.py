from __future__ import print_function
import os
import sys
from pycparser import c_generator, parse_file
import pickle

output_dir = "output/"


def translate_to_c(ast_file_path):

    if os.path.isfile(ast_file_path):
        with open(ast_file_path, 'rb') as ast_file:
            ast = pickle.load(ast_file)
            generator = c_generator.CGenerator()
            print(generator.visit(ast))
    else:
        print ("Invalid file: file could not be opened")


def translate_to_ast(c_file_path):

    if os.path.isfile(c_file_path):
        file_name = c_file_path.split("/")[-1]
        with open(output_dir + file_name + ".ast", 'wb') as file:
            ast = parse_file(c_file_path, use_cpp=True,
                             cpp_path='gcc', cpp_args=['-E', r'-Itools/pycparser/utils/fake_libc_include'])

            pickle.dump(ast, file, protocol=-1)
    else:
        print ("Invalid file: file could not be opened")


def run():
    exit(0)


run()
