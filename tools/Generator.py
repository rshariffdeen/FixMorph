#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
from tools import Emitter
from common import Definitions
from ast import Vector, Parser, Generator as ASTGenerator


def generate_vectors(file_extension, log_file, project):
    Emitter.normal("\t\tgenerating vectors for " + file_extension + " files in " + project.name + "...")
    # Generates an AST file for each file of extension ext

    find_files(project.path, file_extension, log_file)
    with open(log_file, 'r') as file_list:
        source_file = file_list.readline().strip()
        while source_file:
            # Parses it to get useful information and generate vectors
            try:
                function_list, definition_list = ASTGenerator.parse_ast(source_file, use_deckard=True)
                for function_name, begin_line, finish_line in function_list:
                    if source_file not in project.functions.keys():
                        project.functions[source_file] = dict()

                    if function_name not in project.functions[source_file]:
                        project.functions[source_file][function_name] = Vector.Vector(source_file, function_name,
                                                                                      begin_line, finish_line, False)

                    ASTGenerator.get_vars(project, source_file, definition_list)

            except Exception as e:
                error_exit(e, "Unexpected error in parseAST with file:", source_file)
            source_file = file_list.readline().strip()
