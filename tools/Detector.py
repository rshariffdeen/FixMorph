#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
from tools import Emitter, Finder, Logger
from common import Definitions, Values
from ast import Vector, Parser, Generator


def detect_matching_variables(func_name_a, file_a, func_name_c, file_c):
    try:
        Generator.generate_ast_script(Values.Project_A.path + file_a, Values.Project_C.path + file_c, Definitions.FILE_AST_MAP, True)
        # generate_ast_map(Definitions.Pa.path + file_a, Definitions.Pc.path + file_c)
    except Exception as e:
        error_exit(e, "Error at generate_ast_map.")

    function_a = Values.Project_A.function_list[Values.Project_A.path + file_a][func_name_a]
    variable_list_a = function_a.variables.copy()

    while '' in variable_list_a:
        variable_list_a.remove('')

    variable_list_a = [i.split(" ")[-1] for i in variable_list_a]

    # print(Values.Project_C.functions[Values.Project_C.path + file_c])
    Generator.generate_function_list(Values.Project_C, Values.Project_C.path + file_c)

    function_c = Values.Project_C.function_list[Values.Project_C.path + file_c][func_name_c]
    variable_list_c = function_c.variables
    while '' in variable_list_c:
        variable_list_c.remove('')
    json_file_a = Values.Project_A.path + file_a + ".AST"
    ast_a = Parser.AST_from_file(json_file_a)
    json_file_c = Values.Project_C.path + file_c + ".AST"
    ast_c = Parser.AST_from_file(json_file_c)
    ast_map = dict()

    try:
        with open(Definitions.FILE_AST_MAP, "r",) as ast_map_file:
            map_line = ast_map_file.readline().strip()
            while map_line:
                node_a, node_c = clean_parse(map_line, Definitions.TO)
                var_a = id_from_string(node_a)
                var_a = ast_a[var_a].value_calc(Values.Project_A.path + file_a)

                var_c = id_from_string(node_c)
                var_c = ast_c[var_c].value_calc(Values.Project_C.path + file_c)

                if var_a in variable_list_a:
                    if var_a not in ast_map.keys():
                        ast_map[var_a] = dict()
                    if var_c in ast_map[var_a].keys():
                        ast_map[var_a][var_c] += 1
                    else:
                        ast_map[var_a][var_c] = 1
                map_line = ast_map_file.readline().strip()
    except Exception as e:
        error_exit(e, "Unexpected error while parsing ast-map")

    UNKNOWN = "#UNKNOWN#"
    variable_mapping = dict()
    try:
        while variable_list_a:
            var_a = variable_list_a.pop()
            if var_a not in variable_mapping.keys():
                a_name = var_a.split(" ")[-1]
                if a_name in ast_map.keys():
                    max_match = -1
                    best_match = None
                    for var_c in ast_map[a_name].keys():
                        if max_match == -1:
                            max_match = ast_map[a_name][var_c]
                            best_match = var_c
                        elif ast_map[a_name][var_c] > max_match:
                            max_match = ast_map[a_name][var_c]
                            best_match = var_c
                    if best_match:
                        for var_c in variable_list_c:
                            c_name = var_c.split(" ")[-1]
                            if c_name == best_match:
                                variable_mapping[var_a] = var_c
                if var_a not in variable_mapping.keys():
                    variable_mapping[var_a] = UNKNOWN
    except Exception as e:
        error_exit(e, "Unexpected error while mapping vars.")

    with open("output/var-map", "w") as var_map_file:
        for var_a in variable_mapping.keys():
            var_map_file.write(var_a + " -> " + variable_mapping[var_a] + "\n")

    return variable_mapping


def detect_clone_by_distance(vector_list_a, vector_list_c, dist_factor):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    candidate_list_all = dict()
    for vector_a in vector_list_a:
        # Assume vector already created
        file_path_a = vector_a[0]
        matrix_a = vector_a[1]

        possible_candidate_path = file_path_a.replace(Values.Project_A.path, Values.Project_C.path)
        possible_candidate = None
        possible_candidate_distance = 0.0

        vector_c = vector_list_c[0]
        matrix_c = vector_c[1]
        best_distance = Vector.Vector.dist(matrix_a, matrix_c)
        best_vector = vector_c
        distance_matrix = dict()

        # Get best match candidate
        for vector_c in vector_list_c:
            matrix_c = vector_c[1]
            file_path_c = vector_c[0]
            if file_path_c == possible_candidate_path:
                distance = Vector.Vector.dist(matrix_a, matrix_c)
                distance_matrix[file_path_c] = distance
                possible_candidate = vector_c
                possible_candidate_distance = distance
            if matrix_c is not None:
                distance = Vector.Vector.dist(matrix_a, matrix_c)
                distance_matrix[file_path_c] = distance
                if distance < best_distance:
                    best_vector = vector_c
                    best_distance = distance

        # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
        # best_vector = (best_vector[0], best_vector[1], best_distance)
        if possible_candidate is not None:
            candidate_list = [(possible_candidate_path, possible_candidate_distance)]
        else:
            candidate_list = [(best_vector[0], best_distance)]
        candidate_distance = dict()
        candidate_location = dict()

        # Collect all vectors within range best_distance - 2 x best_distance
        for vector_c in vector_list_c:
            matrix_c = vector_c[1]
            file_path_c = vector_c[0]
            if vector_c is not None:
                if vector_c[0] != best_vector[0]:
                    if matrix_c is not None:
                        distance = distance_matrix[file_path_c]
                        if distance <= dist_factor * best_distance:
                            # vector_c = (vector_c[0], vector_c[1], distance)
                            candidate_list.append((vector_c[0], distance))

        candidate_list_all[file_path_a] = candidate_list

    return candidate_list_all


def detect_struct_clones():
    extension = "*struct*\.vec"
    vector_list_a = Finder.search_vector_list(Values.Project_A, extension, 'struct')
    vector_list_c = Finder.search_vector_list(Values.Project_C, extension, 'struct')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    candidate_list_all = detect_clone_by_distance(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".struct_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".struct_")
        vector_source_a = str(vector_source_a).replace(Values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(Values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        Emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        Emitter.success("\t\t\tStructure: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        Emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
    return clone_list


def detect_enum_clones():
    extension = "*enum*\.vec"
    vector_list_a = Finder.search_vector_list(Values.Project_A, extension, 'enum')
    vector_list_c = Finder.search_vector_list(Values.Project_C, extension, 'enum')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    candidate_list_all = detect_clone_by_distance(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".enum_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".enum_")
        vector_source_a = str(vector_source_a).replace(Values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(Values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        Emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        Emitter.success("\t\t\tEnum Definition: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        Emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
    return clone_list


def detect_function_clones():
    extension = "*func*\.vec"
    vector_list_a = Finder.search_vector_list(Values.Project_A, extension, 'function')
    vector_list_c = Finder.search_vector_list(Values.Project_C, extension, 'function')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    candidate_list_all = detect_clone_by_distance(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".func_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".func_")
        vector_source_a = str(vector_source_a).replace(Values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(Values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        Emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        Emitter.success("\t\t\tFunction: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        Emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
    return clone_list


def detect_decl_clones():
    extension = "*var*\.vec"
    vector_list_a = Finder.search_vector_list(Values.Project_A, extension, 'global variable')
    vector_list_c = Finder.search_vector_list(Values.Project_C, extension, 'global variable')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    candidate_list_all = detect_clone_by_distance(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".var_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".var_")
        vector_source_a = str(vector_source_a).replace(Values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(Values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        Emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        Emitter.success("\t\t\tDeclaration: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        Emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
    return clone_list


def detect_clones():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    struct_clones = list()
    enum_clones = list()
    decl_clones = list()
    function_clones = list()
    if Values.IS_STRUCT:
        Emitter.sub_sub_title("Finding clone structures in Target")
        struct_clones = detect_struct_clones()
        # print(struct_clones)
    if Values.IS_ENUM:
        Emitter.sub_sub_title("Finding clone enum in Target")
        enum_clones = detect_enum_clones()
        # print(enum_clones)
    if Values.IS_FUNCTION:
        Emitter.sub_sub_title("Finding clone functions in Target")
        function_clones = detect_function_clones()
        # print(function_clones)
    if Values.IS_TYPEDEC:
        Emitter.sub_sub_title("Finding clone variable declaration in Target")
        decl_clones = detect_decl_clones()
        # print(function_clones)
    clone_list = struct_clones + enum_clones + function_clones + decl_clones
    return clone_list


# def find_clone_old():
#     extension = "*\.c\.*\.vec"
#     clone_list = []
#     vector_list_a = Finder.search_vector_list(Values.Project_A, extension)
#     vector_list_c = Finder.search_vector_list(Values.Project_C, extension)
#     factor = 2
#     UNKNOWN = "#UNKNOWN#"
#     Emitter.normal("\tfinding clones for edited functions:\n")
#     for vector in vector_list_a:
#         # Assume vector already created
#         file_path = vector[0]
#         vector_a = vector[1]
#         best_match = vector_list_c[0]
#         best_distance = Vector.Vector.dist(vector_a, best_match[1])
#         distance_matrix = dict()
#         count_unknown = dict()
#         count_vars = dict()
#         var_map_list = dict()
#
#         # Get best match candidate
#         for j in vector_list_c:
#             vector_c = j[1]
#             if vector_c is not None:
#                 distance = Vector.Vector.dist(vector_a, j[1])
#                 distance_matrix[j[0]] = distance
#                 if distance < best_distance:
#                     best_match = j
#                     best_distance = distance
#
#         # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
#         candidate_list = [best_match]
#         candidate_distance = dict()
#         candidate_location = dict()
#
#         # Collect all vectors within range best_distance - 2 x best_distance
#         for j in vector_list_c:
#             vector_c = j[1]
#             if vector_c is not None:
#                 if j != best_match:
#                     distance = distance_matrix[j[0]]
#                     if distance <= factor * best_distance:
#                         candidate_list.append(j)
#
#         # We go up to -4 to remove the ".vec" part [filepath.function.vec]
#         fa = file_path.replace(Values.Project_A.path, "")[:-4].split(".")
#         f_a = fa[-1]
#         file_a = ".".join(fa[:-1])
#         Emitter.normal("\t\tFinding match for " + f_a + " in $Pa/" + file_a + ":")
#
#         best_candidate = ''
#         best_count = 0
#         best_distance = 0
#         best_prop = 0
#         var_map = ''
#
#         # TODO: Correct once I have appropriate only function comparison
#         for candidate in candidate_list:
#             fc = candidate[0].replace(Values.Project_C.path, "")[:-4].split(".")
#             f_c = fc[-1]
#             candidate_distance[f_c] = distance_matrix[candidate[0]]
#             file_c = ".".join(fc[:-1])
#             candidate_location[f_c] = file_c
#             d_c = str(distance_matrix[candidate[0]])
#             Emitter.information("\tPossible match for " + f_a + " in $Pa/" + file_a + ":")
#             Emitter.information("\t\tFunction: " + f_c + " in $Pc/" + file_c)
#             Emitter.information("\t\tDistance: " + d_c + "\n")
#             Emitter.information("\tVariable mapping from " + f_a + " to " + f_c + ":")
#             count_unknown[f_c] = 0
#             count_vars[f_c] = 0
#             try:
#                 var_map_list[f_c] = detect_matching_variables(f_a, file_a, f_c, file_c)
#             except Exception as e:
#                 error_exit(e, "Unexpected error while matching variables.")
#             with open('output/var-map', 'r', errors='replace') as mapped:
#                 mapping = mapped.readline().strip()
#                 while mapping:
#                     Emitter.information("\t\t" + mapping)
#                     if UNKNOWN in mapping:
#                         count_unknown[f_c] += 1
#                     count_vars[f_c] += 1
#                     mapping = mapped.readline().strip()
#             best_func_name = f_c
#             best_count = count_unknown[best_func_name]
#             best_distance = candidate_distance[best_func_name]
#             best_prop = count_unknown[best_func_name] / count_vars[best_func_name]
#             var_map = var_map_list[best_func_name]
#
#         for candidate in candidate_distance:
#             if count_unknown[candidate] < best_count:
#                 best_count = count_unknown[candidate]
#                 best_candidate = candidate
#                 best_distance = candidate_distance[candidate]
#                 best_prop = count_unknown[candidate] / count_vars[candidate]
#                 var_map = var_map_list[candidate]
#             elif count_unknown[candidate] == best_count:
#                 prop = count_unknown[candidate] / count_vars[candidate]
#                 if prop < best_prop:
#                     best_candidate = candidate
#                     best_distance = candidate_distance[candidate]
#                     best_prop = prop
#                     var_map = var_map_list[candidate]
#                 elif prop == best_prop:
#                     if candidate_distance[candidate] <= best_distance:
#                         best_candidate = candidate
#                         best_distance = candidate_distance[candidate]
#                         var_map = var_map_list[candidate]
#
#         Emitter.success("\t\t\tFunction: " + best_candidate + " in $Pc/" + str(candidate_location[best_candidate]))
#         Emitter.success("\t\t\tDistance: " + str(best_distance) + "\n")
#
#         clone_list.append((Values.Project_A.function_list[Values.Project_A.path + file_a][f_a],
#                                Values.Project_C.function_list[Values.Project_C.path + candidate_location[best_candidate]][best_candidate], var_map))
#
#     return clone_list

#
# def find_diff_files():
#     extensions = get_extensions(Definitions.Pa.path, excluded_extensions_pa)
#     extensions = extensions.union(get_extensions(Definitions.Pb.path, excluded_extensions_pb))
#     with open(excluded_extensions, 'w', errors='replace') as exclusions:
#         for pattern in extensions:
#             exclusions.write(pattern + "\n")
#     # TODO: Include cases where a file is added or removed
#     c = "diff -ENZBbwqr " + Definitions.Pa.path + " " + Definitions.Pb.path + " -X " + excluded_extensions + "> output/diff; "
#     c += "cat output/diff | grep -P '\.c and ' > output/diff_C; "
#     c += "cat output/diff | grep -P '\.h and ' > output/diff_H; "
#     exec_com(c, False)
#
#
#
#
# def generate_vector_for_extension(file_extension, output, is_header=False):
#
#     Emitter.blue("Generate vectors for " + file_extension + " files in " + Definitions.Pc.name + "...")
#     # Generates an AST file for each file of extension ext
#     find_files(Definitions.Pc.path, file_extension, output)
#     with open(output, 'r', errors='replace') as file_list:
#         file_name = file_l
#         ist.readline().strip()
#         while file_name:
#             # Parses it to get useful information and generate vectors
#             try:
#                 Generator.parseAST(file_name, Definitions.Pc, use_deckard=True, is_header=is_header)
#             except Exception as e:
#                 err_exit(e, "Unexpected error in parseAST with file:", file_name)
#             file_name = file_list.readline().strip()
#
#
# def generate_vectors():
#     # Generates an vector file for each .h file
#     generate_vector_for_extension("*\.h", "output/Hfiles", is_header=True)
#     print("\n")
#     # Generates an vector file for each .c file
#     generate_vector_for_extension("*\.c", "output/Cfiles", is_header=False)
#
#
# def get_vector_list(project, extension):
#     if "c" in extension:
#         rxt = "C"
#     else:
#         rxt = "h"
#
#     Emitter.blue("Getting vectors for " + rxt + " files in " + project.name + "...")
#     filepath = "output/vectors_" + rxt + "_" + project.name
#     find_files(project.path, extension, filepath)
#     with open(filepath, "r", errors='replace') as file:
#         files = [vec.strip() for vec in file.readlines()]
#     vecs = []
#     for i in range(len(files)):
#         with open(files[i], 'r', errors='replace') as vec:
#             fl = vec.readline()
#             if fl:
#                 v = [int(s) for s in vec.readline().strip().split(" ")]
#                 v = Vector.Vector.normed(v)
#                 vecs.append((files[i], v))
#     return vecs
#
#
# def clone_detection_header_files():
#     extension = "*\.h\.vec"
#     candidate_list = []
#     vector_list_a = get_vector_list(Definitions.Pa, extension)
#     if len(vector_list_a) == 0:
#         Emitter.blue(" - nothing to do -")
#         return candidate_list
#     vector_list_c = get_vector_list(Definitions.Pc, extension)
#     factor = 2
#
#     Emitter.blue("Declaration mapping for *.h files")
#     for vector_a in vector_list_a:
#         best_vector = vector_list_c[0]
#         min_distance = Vector.Vector.dist(vector_a[1], best_vector[1])
#         dist = dict()
#
#         for vector_c in vector_list_c:
#             distance = Vector.Vector.dist(vector_a[1], vector_c[1])
#             dist[vector_c[0]] = distance
#             if distance < min_distance:
#                 best_vector = vector_c
#                 min_distance = distance
#
#         potential_list = [(best_vector, min_distance)]
#         for vector_c in vector_list_c:
#             if vector_c != best_vector:
#                 distance = dist[vector_c[0]]
#                 if distance <= factor * min_distance:
#                     potential_list.append((vector_c, distance))
#
#         declaration_map_list = list()
#         match_score_list = list()
#         match_count_list = list()
#         modified_header_file = vector_a[0].replace(Definitions.Pa.path, "")[:-4]
#
#         for potential_iterator in range(len(potential_list)):
#             potential_candidate = potential_list[potential_iterator][0]
#             potential_candidate_file = potential_candidate[0].replace(Definitions.Pc.path, "")[:-4]
#             vector_distance = str(potential_list[potential_iterator][1])
#             Emitter.blue("\tPossible match for " + modified_header_file + " in Pa:")
#             Emitter.blue("\t\tFile: " + potential_candidate_file + " in Pc")
#             Emitter.blue("\t\tDistance: " + vector_distance + "\n")
#             Emitter.blue("\tDeclaration mapping from " + modified_header_file + " to " + potential_candidate_file + ":")
#             try:
#                 declaration_map, match_count, edit_count = detect_matching_declarations(modified_header_file, potential_candidate_file)
#                 declaration_map_list.append(declaration_map)
#                 match_score_list.append((match_count - edit_count) / (match_count + edit_count))
#                 match_count_list.append(match_count)
#             except Exception as e:
#                 err_exit(e, "Unexpected error while matching declarations.")
#             with open('output/var-map', 'r', errors='replace') as mapped:
#                 mapping = mapped.readline().strip()
#                 while mapping:
#                     Emitter.grey("\t\t" + mapping)
#                     mapping = mapped.readline().strip()
#
#         best_score = match_score_list[0]
#         best_candidate = potential_list[0][0]
#         min_distance = potential_list[0][1]
#         best_match_count = match_count_list[0]
#         best_index = [0]
#
#         for potential_iterator in range(1, len(potential_list)):
#             score = match_score_list[potential_iterator]
#             distance = potential_list[potential_iterator][1]
#             match_count = match_count_list[potential_iterator]
#             if score > best_score:
#                 best_score = score
#                 best_index = [potential_iterator]
#             elif score == best_score:
#                 if distance < min_distance:
#                     min_distance = distance
#                     best_index = [potential_iterator]
#                 elif distance == min_distance:
#                     if match_count > best_match_count:
#                         best_match_count = match_count
#                         best_index = [potential_iterator]
#                     else:
#                         best_index.append(potential_iterator)
#         # Potentially many identical matches
#         potential_count = len(best_index)
#         m = min(1, potential_count)
#         Emitter.success("\t" + str(potential_count) + " match" + "es" * m + " for " + modified_header_file)
#         for index in best_index:
#             file_c = potential_list[index][0][0][:-4].replace(Definitions.Pc.path, "")
#             d_c = str(potential_list[index][1])
#             decl_map = declaration_map_list[index]
#             Emitter.success("\t\tMatch for " + modified_header_file + " in Pa:")
#             Emitter.blue("\t\tFile: " + file_c + " in Pc.")
#             Emitter.blue("\t\tDistance: " + d_c + ".\n")
#             Emitter.blue("\t\tMatch Score: " + d_c + ".\n")
#             # Print.green((Common.Pa.path + file_a, Pc.path + file_c, var_map))
#             candidate_list.append((Definitions.Pa.path + modified_header_file, Definitions.Pc.path + file_c, decl_map))
#     return candidate_list
#
#

#
# def detect_c_files():
#     extension = "*\.c\.*\.vec"
#     candidate_list = []
#     vector_list_a = Finder.search_vector_list(Values.Project_A, extension)
#     print(vector_list_a)
#     exit()
#
#     if len(vector_list_a) == 0:
#         Emitter.normal("\t - nothing to do -")
#         return candidate_list
#
#     vector_list_c = Finder.search_vector_list(Values.Project_C, extension)
#     Emitter.normal("\tVariable mapping...\n")
#
#     UNKNOWN = "#UNKNOWN#"
#     factor = 2
#
#     for i in vector_list_a:
#         best = vector_list_c[0]
#         best_d = Vector.Vector.dist(i[1], best[1])
#         dist = dict()
#
#         # Get best match candidate
#         for j in vector_list_c:
#             d = Vector.Vector.dist(i[1], j[1])
#             dist[j[0]] = d
#             if d < best_d:
#                 best = j
#                 best_d = d
#
#         # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
#         candidates = [best]
#         candidates_d = [best_d]
#         for j in vector_list_c:
#             if j != best:
#                 d = dist[j[0]]
#                 if d <= factor * best_d:
#                     candidates.append(j)
#                     candidates_d.append(d)
#
#         count_unknown = [0] * len(candidates)
#         count_vars = [0] * len(candidates)
#         var_maps = []
#
#         # We go up to -4 to remove the ".vec" part [filepath.function.vec]
#         fa = i[0].replace(Values.Project_A.path, "")[:-4].split(".")
#         f_a = fa[-1]
#         file_a = ".".join(fa[:-1])
#
#         # TODO: Correct once I have appropriate only function comparison
#         for k in range(len(candidates)):
#             candidate = candidates[k]
#             fc = candidate[0].replace(Values.Project_C.path, "")[:-4].split(".")
#             f_c = fc[-1]
#             file_c = ".".join(fc[:-1])
#             d_c = str(candidates_d[k])
#             Emitter.normal("\tPossible match for " + f_a + " in $Pa/" + file_a + ":")
#             Emitter.normal("\t\tFunction: " + f_c + " in $Pc/" + file_c)
#             Emitter.normal("\t\tDistance: " + d_c + "\n")
#             Emitter.normal("\tVariable mapping from " + f_a + " to " + f_c + ":")
#             try:
#                 var_map = detect_matching_variables(f_a, file_a, f_c, file_c)
#                 var_maps.append(var_map)
#             except Exception as e:
#                 error_exit(e, "Unexpected error while matching variables.")
#             with open('output/var-map', 'r', errors='replace') as mapped:
#                 mapping = mapped.readline().strip()
#                 while mapping:
#                     Emitter.special("\t\t" + mapping)
#                     if UNKNOWN in mapping:
#                         count_unknown[k] += 1
#                     count_vars[k] += 1
#                     mapping = mapped.readline().strip()
#
#         best_count = count_unknown[0]
#         best = candidates[0]
#         best_d = candidates_d[0]
#         best_prop = count_unknown[0] / count_vars[0]
#         var_map = var_maps[0]
#         for k in range(1, len(count_unknown)):
#             if count_vars[k] > 0:
#                 if count_unknown[k] < best_count:
#                     best_count = count_unknown[k]
#                     best = candidates[k]
#                     best_d = candidates_d[k]
#                     best_prop = count_unknown[k] / count_vars[k]
#                     var_map = var_maps[k]
#                 elif count_unknown[k] == best_count:
#                     prop = count_unknown[k] / count_vars[k]
#                     if prop < best_prop:
#                         best = candidates[k]
#                         best_d = candidates_d[k]
#                         best_prop = prop
#                         var_map = var_maps[k]
#                     elif prop == best_prop:
#                         if candidates_d[k] <= best_d:
#                             best = candidates[k]
#                             best_d = candidates_d[k]
#                             var_map = var_maps[k]
#
#         fc = best[0].replace(Values.Project_C.path, "")[:-4].split(".")
#         f_c = fc[-1]
#         file_c = ".".join(fc[:-1])
#         d_c = str(best_d)
#         Emitter.success("\t\tBest match for " + f_a + " in $Pa/" + file_a + ":")
#         Emitter.normal("\t\tFunction: " + f_c + " in $Pc/" + file_c)
#         Emitter.normal("\t\tDistance: " + d_c + "\n")
#
#         candidate_list.append((Values.Project_A.function_list[Values.Project_A.path + file_a][f_a],
#                                Values.Project_C.function_list[Values.Project_C.path + file_c][f_c], var_map))
#     return candidate_list


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])


# def detect_matching_declarations(file_a, file_c):
#     try:
#         generate_ast_map(Definitions.Pa.path + file_a, Definitions.Pc.path + file_c)
#     except Exception as e:
#         err_exit(e, "Error at generate_ast_map.")
#
#     ast_map = dict()
#
#     try:
#         with open("output/ast-map", "r", errors="replace") as ast_map_file:
#             map_lines = ast_map_file.readlines()
#     except Exception as e:
#         err_exit(e, "Unexpected error parsing ast-map in detect_matching declarations")
#
#     match_count = 0
#     edit_count = 0
#     for line in map_lines:
#         line = line.strip()
#         if len(line) > 6 and line[:5] == "Match":
#             line = clean_parse(line[6:], Definitions.TO)
#             if "Decl" not in line[0]:
#                 continue
#             match_count += 1
#             ast_map[line[0]] = line[1]
#         else:
#             edit_count += 1
#
#     with open("output/var-map", "w", errors='replace') as var_map_file:
#         for var_a in ast_map.keys():
#             var_map_file.write(var_a + " -> " + ast_map[var_a] + "\n")
#
#     return ast_map, match_count, edit_count
#
#


def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content) - 1:
                if content[i] == "\\":
                    i += 2
                elif content[i] == "\"":
                    i += 1
                    break
                else:
                    i += 1
            prefix = content[:i]
            rest = content[i:].split(separator)
            node1 = prefix + rest[0]
            node2 = separator.join(rest[1:])
            return [node1, node2]
        i += 1
    # If all the above fails (it shouldn't), hope for some luck:
    nodes = content.split(separator)
    half = len(nodes) // 2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]
