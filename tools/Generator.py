#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
from tools import Emitter
from common import Definitions
from ast import Vector, Parser, Generator


def generate_vectors(file_extension, log_file, project, diff_list=None):
    Emitter.normal("\t\tgenerating vectors for " + file_extension + " files in " + project.name + "...")
    # Generates an AST file for each file of extension ext
    if diff_list is None:
        find_files(project.path, file_extension, log_file)
        with open(log_file, 'r') as file_list:
            file_name = file_list.readline().strip()
            while file_name:
                # Parses it to get useful information and generate vectors
                try:
                    Generator.parse_ast(file_name, use_deckard=True)
                except Exception as e:
                    error_exit(e, "Unexpected error in parseAST with file:", file_name)
                file_name = file_list.readline().strip()
    else:
        with open(diff_list, 'r') as file_list:
            file_name = file_list.readline().strip()
            while file_name:
                # Parses it to get useful information and generate vectors
                try:
                    Generator.parse_ast(file_name, use_deckard=True)
                except Exception as e:
                    error_exit(e, "Unexpected error in parseAST with file:", file_name)
                file_name = file_list.readline().strip()
