#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
from tools import Emitter
from ast import Vector, Parser, Generator as ASTGenerator
from common import Definitions
from common.Utilities import error_exit, clean_parse


def collect_instruction_list(script_file_path):
    instruction_list = list()
    inserted_node_list = list()
    map_ab = dict()
    with open(script_file_path, 'r') as script:
        line = script.readline().strip()
        while line:
            line = line.split(" ")
            # Special case: Update and Move nodeA into nodeB2
            if len(line) > 3 and line[0] == Definitions.UPDATE and line[1] == Definitions.AND and \
                    line[2] == Definitions.MOVE:
                instruction = Definitions.UPDATEMOVE
                content = " ".join(line[3:])

            else:
                instruction = line[0]
                content = " ".join(line[1:])
            # Match nodeA to nodeB
            if instruction == Definitions.MATCH:
                try:
                    node_a, node_b = clean_parse(content, Definitions.TO)
                    map_ab[node_b] = node_a
                except Exception as e:
                    error_exit(e, "Something went wrong in MATCH (AB).", line, instruction, content)
            # Update nodeA to nodeB (only care about value)
            elif instruction == Definitions.UPDATE:
                try:
                    node_a, node_b = clean_parse(content, Definitions.TO)
                    if "TypeLoc" in node_a:
                        continue
                    instruction_list.append((instruction, node_a, node_b))
                except Exception as e:
                    error_exit(e, "Something went wrong in UPDATE.")
            # Delete nodeA
            elif instruction == Definitions.DELETE:
                try:
                    node_a = content
                    instruction_list.append((instruction, node_a))
                except Exception as e:
                    error_exit(e, "Something went wrong in DELETE.")
            # Move nodeA into nodeB at pos
            elif instruction == Definitions.MOVE:
                try:
                    node_a, node_b = clean_parse(content, Definitions.INTO)
                    node_b_at = node_b.split(Definitions.AT)
                    node_b = Definitions.AT.join(node_b_at[:-1])
                    pos = node_b_at[-1]
                    instruction_list.append((instruction, node_a, node_b, pos))
                except Exception as e:
                    error_exit(e, "Something went wrong in MOVE.")
            # Update nodeA into matching node in B and move into nodeB at pos
            elif instruction == Definitions.UPDATEMOVE:
                try:
                    node_a, node_b = clean_parse(content, Definitions.INTO)
                    node_b_at = node_b.split(Definitions.AT)
                    node_b = Definitions.AT.join(node_b_at[:-1])
                    pos = node_b_at[-1]
                    instruction_list.append((instruction, node_a, node_b, pos))
                except Exception as e:
                    error_exit(e, "Something went wrong in MOVE.")
                    # Insert nodeB1 into nodeB2 at pos
            elif instruction == Definitions.INSERT:
                try:
                    node_a, node_b = clean_parse(content, Definitions.INTO)
                    node_b_at = node_b.split(Definitions.AT)
                    node_b = Definitions.AT.join(node_b_at[:-1])
                    pos = node_b_at[-1]
                    instruction_list.append((instruction, node_a, node_b, pos))
                    inserted_node_list.append(node_a)
                except Exception as e:
                    error_exit(e, "Something went wrong in INSERT.")
            line = script.readline().strip()
    return instruction_list, inserted_node_list, map_ab


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
                    if source_file not in project.function_list.keys():
                        project.function_list[source_file] = dict()

                    if function_name not in project.function_list[source_file]:
                        project.function_list[source_file][function_name] = Vector.Vector(source_file, function_name,
                                                                                      begin_line, finish_line, False)

                    ASTGenerator.get_vars(project, source_file, definition_list)

            except Exception as e:
                error_exit(e, "Unexpected error in parseAST with file:", source_file)
            source_file = file_list.readline().strip()

