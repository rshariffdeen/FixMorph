from __future__ import print_function
import os
import sys
from pycparser import c_generator, parse_file
import pickle
import subprocess as sub

output_dir = "output/"

file_list = list()
function_list = list()


def exec_command(command):
    #print(command)
    p = sub.Popen([command], stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = p.communicate()

    if p.returncode != 0:
        print ("ERROR")
        print(errors)
        exit(-1)
    return output


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




def initialize(source_a, function_a, source_b, function_b, source_c, function_c):
    global file_list, function_list
    file_list.append(source_a)
    file_list.append(source_b)
    file_list.append(source_c)

    function_list.append(function_a)
    function_list.append(function_b)
    function_list.append(function_c)


def generate_ast_files():
    for source_file in file_list:
        translate_to_ast(source_file)





def transplant(source_a, function_a, source_b, function_b, source_c, function_c):
    initialize(source_a, function_a, source_b, function_b, source_c, function_c)
    generate_ast_files()

    exit(0)

