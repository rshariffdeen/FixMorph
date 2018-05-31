from __future__ import print_function
import os
import sys
from pycparser import parse_file
import pickle
output_dir = "output/"


def translate_to_ast(c_file_path):

    if os.path.isfile(c_file_path):
        file_name = c_file_path.split("/")[-1]
        with open(output_dir + file_name + ".ast", 'wb') as file:
            ast = parse_file(c_file_path, use_cpp=True,
                         cpp_path='gcc',
                         cpp_args=['-E', r'-Itools/pycparser/utils/fake_libc_include'])

            pickle.dump(ast, file, protocol=-1)
    else:
        print ("Invalid file: file could not be opened")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        translate_to_ast(sys.argv[1])
    else:
        print("Please provide a filename as argument")
