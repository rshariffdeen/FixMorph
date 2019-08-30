#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from common.Utilities import execute_command, error_exit, find_files, get_file_extension_list
import Emitter
from common import Definitions
from ast import Vector, Parser, Generator

excluded_extensions_pa = "output/excluded-extensions-pa"
excluded_extensions_pb = "output/excluded-extensions-pb"
excluded_extensions = 'output/excluded-extensions'


def find_diff_files():
    extensions = get_extensions(Definitions.Pa.path, excluded_extensions_pa)
    extensions = extensions.union(get_extensions(Definitions.Pb.path, excluded_extensions_pb))
    with open(excluded_extensions, 'w', errors='replace') as exclusions:
        for pattern in extensions:
            exclusions.write(pattern + "\n")
    # TODO: Include cases where a file is added or removed
    c = "diff -ENZBbwqr " + Definitions.Pa.path + " " + Definitions.Pb.path + " -X " + excluded_extensions + "> output/diff; "
    c += "cat output/diff | grep -P '\.c and ' > output/diff_C; "
    c += "cat output/diff | grep -P '\.h and ' > output/diff_H; "
    exec_com(c, False)




def generate_vector_for_extension(file_extension, output, is_header=False):

    Emitter.blue("Generate vectors for " + file_extension + " files in " + Definitions.Pc.name + "...")
    # Generates an AST file for each file of extension ext
    find_files(Definitions.Pc.path, file_extension, output)
    with open(output, 'r', errors='replace') as file_list:
        file_name = file_list.readline().strip()
        while file_name:
            # Parses it to get useful information and generate vectors
            try:
                Generator.parseAST(file_name, Definitions.Pc, use_deckard=True, is_header=is_header)
            except Exception as e:
                err_exit(e, "Unexpected error in parseAST with file:", file_name)
            file_name = file_list.readline().strip()


def generate_vectors():
    # Generates an vector file for each .h file
    generate_vector_for_extension("*\.h", "output/Hfiles", is_header=True)
    print("\n")
    # Generates an vector file for each .c file
    generate_vector_for_extension("*\.c", "output/Cfiles", is_header=False)


def get_vector_list(project, extension):
    if "c" in extension:
        rxt = "C"
    else:
        rxt = "h"

    Emitter.blue("Getting vectors for " + rxt + " files in " + project.name + "...")
    filepath = "output/vectors_" + rxt + "_" + project.name
    find_files(project.path, extension, filepath)
    with open(filepath, "r", errors='replace') as file:
        files = [vec.strip() for vec in file.readlines()]
    vecs = []
    for i in range(len(files)):
        with open(files[i], 'r', errors='replace') as vec:
            fl = vec.readline()
            if fl:
                v = [int(s) for s in vec.readline().strip().split(" ")]
                v = Vector.Vector.normed(v)
                vecs.append((files[i], v))
    return vecs


def clone_detection_header_files():
    extension = "*\.h\.vec"
    candidate_list = []
    vector_list_a = get_vector_list(Definitions.Pa, extension)
    if len(vector_list_a) == 0:
        Emitter.blue(" - nothing to do -")
        return candidate_list
    vector_list_c = get_vector_list(Definitions.Pc, extension)
    factor = 2

    Emitter.blue("Declaration mapping for *.h files")
    for vector_a in vector_list_a:
        best_vector = vector_list_c[0]
        min_distance = Vector.Vector.dist(vector_a[1], best_vector[1])
        dist = dict()

        for vector_c in vector_list_c:
            distance = Vector.Vector.dist(vector_a[1], vector_c[1])
            dist[vector_c[0]] = distance
            if distance < min_distance:
                best_vector = vector_c
                min_distance = distance

        potential_list = [(best_vector, min_distance)]
        for vector_c in vector_list_c:
            if vector_c != best_vector:
                distance = dist[vector_c[0]]
                if distance <= factor * min_distance:
                    potential_list.append((vector_c, distance))

        declaration_map_list = list()
        match_score_list = list()
        match_count_list = list()
        modified_header_file = vector_a[0].replace(Definitions.Pa.path, "")[:-4]

        for potential_iterator in range(len(potential_list)):
            potential_candidate = potential_list[potential_iterator][0]
            potential_candidate_file = potential_candidate[0].replace(Definitions.Pc.path, "")[:-4]
            vector_distance = str(potential_list[potential_iterator][1])
            Emitter.blue("\tPossible match for " + modified_header_file + " in Pa:")
            Emitter.blue("\t\tFile: " + potential_candidate_file + " in Pc")
            Emitter.blue("\t\tDistance: " + vector_distance + "\n")
            Emitter.blue("\tDeclaration mapping from " + modified_header_file + " to " + potential_candidate_file + ":")
            try:
                declaration_map, match_count, edit_count = detect_matching_declarations(modified_header_file, potential_candidate_file)
                declaration_map_list.append(declaration_map)
                match_score_list.append((match_count - edit_count) / (match_count + edit_count))
                match_count_list.append(match_count)
            except Exception as e:
                err_exit(e, "Unexpected error while matching declarations.")
            with open('output/var-map', 'r', errors='replace') as mapped:
                mapping = mapped.readline().strip()
                while mapping:
                    Emitter.grey("\t\t" + mapping)
                    mapping = mapped.readline().strip()

        best_score = match_score_list[0]
        best_candidate = potential_list[0][0]
        min_distance = potential_list[0][1]
        best_match_count = match_count_list[0]
        best_index = [0]

        for potential_iterator in range(1, len(potential_list)):
            score = match_score_list[potential_iterator]
            distance = potential_list[potential_iterator][1]
            match_count = match_count_list[potential_iterator]
            if score > best_score:
                best_score = score
                best_index = [potential_iterator]
            elif score == best_score:
                if distance < min_distance:
                    min_distance = distance
                    best_index = [potential_iterator]
                elif distance == min_distance:
                    if match_count > best_match_count:
                        best_match_count = match_count
                        best_index = [potential_iterator]
                    else:
                        best_index.append(potential_iterator)
        # Potentially many identical matches
        potential_count = len(best_index)
        m = min(1, potential_count)
        Emitter.success("\t" + str(potential_count) + " match" + "es" * m + " for " + modified_header_file)
        for index in best_index:
            file_c = potential_list[index][0][0][:-4].replace(Definitions.Pc.path, "")
            d_c = str(potential_list[index][1])
            decl_map = declaration_map_list[index]
            Emitter.success("\t\tMatch for " + modified_header_file + " in Pa:")
            Emitter.blue("\t\tFile: " + file_c + " in Pc.")
            Emitter.blue("\t\tDistance: " + d_c + ".\n")
            Emitter.blue("\t\tMatch Score: " + d_c + ".\n")
            # Print.green((Common.Pa.path + file_a, Pc.path + file_c, var_map))
            candidate_list.append((Definitions.Pa.path + modified_header_file, Definitions.Pc.path + file_c, decl_map))
    return candidate_list


def clone_detection_for_c_files():

    c_ext = "*\.c\.*\.vec"
    candidate_list = []
    vector_list_a = get_vector_list(Definitions.Pa, c_ext)
    if len(vector_list_a) == 0:
        Emitter.blue("\t - nothing to do -")
        return candidate_list

    vector_list_c = get_vector_list(Definitions.Pc, c_ext)
    Emitter.blue("Variable mapping...\n")


    UNKNOWN = "#UNKNOWN#"
    factor = 2

    for i in vector_list_a:
        best = vector_list_c[0]
        best_d = Vector.Vector.dist(i[1], best[1])
        dist = dict()

        # Get best match candidate
        for j in vector_list_c:
            d = Vector.Vector.dist(i[1], j[1])
            dist[j[0]] = d
            if d < best_d:
                best = j
                best_d = d

        # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
        candidates = [best]
        candidates_d = [best_d]
        for j in vector_list_c:
            if j != best:
                d = dist[j[0]]
                if d <= factor * best_d:
                    candidates.append(j)
                    candidates_d.append(d)

        count_unknown = [0] * len(candidates)
        count_vars = [0] * len(candidates)
        var_maps = []

        # We go up to -4 to remove the ".vec" part [filepath.function.vec]
        fa = i[0].replace(Definitions.Pa.path, "")[:-4].split(".")
        f_a = fa[-1]
        file_a = ".".join(fa[:-1])

        # TODO: Correct once I have appropriate only function comparison
        for k in range(len(candidates)):
            candidate = candidates[k]
            fc = candidate[0].replace(Definitions.Pc.path, "")[:-4].split(".")
            f_c = fc[-1]
            file_c = ".".join(fc[:-1])
            d_c = str(candidates_d[k])
            Emitter.blue("\tPossible match for " + f_a + " in $Pa/" + file_a + \
                       ":")
            Emitter.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
            Emitter.blue("\t\tDistance: " + d_c + "\n")
            Emitter.blue("\tVariable mapping from " + f_a + " to " + f_c + ":")
            try:
                var_map = detect_matching_variables(f_a, file_a, f_c, file_c)
                var_maps.append(var_map)
            except Exception as e:
                err_exit(e, "Unexpected error while matching variables.")
            with open('output/var-map', 'r', errors='replace') as mapped:
                mapping = mapped.readline().strip()
                while mapping:
                    Emitter.grey("\t\t" + mapping)
                    if UNKNOWN in mapping:
                        count_unknown[k] += 1
                    count_vars[k] += 1
                    mapping = mapped.readline().strip()

        best_count = count_unknown[0]
        best = candidates[0]
        best_d = candidates_d[0]
        best_prop = count_unknown[0] / count_vars[0]
        var_map = var_maps[0]
        for k in range(1, len(count_unknown)):
            if count_vars[k] > 0:
                if count_unknown[k] < best_count:
                    best_count = count_unknown[k]
                    best = candidates[k]
                    best_d = candidates_d[k]
                    best_prop = count_unknown[k] / count_vars[k]
                    var_map = var_maps[k]
                elif count_unknown[k] == best_count:
                    prop = count_unknown[k] / count_vars[k]
                    if prop < best_prop:
                        best = candidates[k]
                        best_d = candidates_d[k]
                        best_prop = prop
                        var_map = var_maps[k]
                    elif prop == best_prop:
                        if candidates_d[k] <= best_d:
                            best = candidates[k]
                            best_d = candidates_d[k]
                            var_map = var_maps[k]

        fc = best[0].replace(Definitions.Pc.path, "")[:-4].split(".")
        f_c = fc[-1]
        file_c = ".".join(fc[:-1])
        d_c = str(best_d)
        Emitter.success("\t\tBest match for " + f_a + " in $Pa/" + file_a + ":")
        Emitter.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
        Emitter.blue("\t\tDistance: " + d_c + "\n")

        candidate_list.append((Definitions.Pa.functions[Definitions.Pa.path + file_a][f_a],
                               Definitions.Pc.functions[Definitions.Pc.path + file_c][f_c], var_map))
    return candidate_list


def generate_ast_map(source_a, source_b):
    command = Definitions.DIFF_COMMAND + "-dump-matches " + source_a + " " + source_b
    if source_a[-1] == "h":
        command += " --"
    command += " 2>> output/errors_clang_diff"
    command += "| grep -P '^Match ' | grep -P '^Match ' > output/ast-map"
    try:
        exec_com(command, False)
    except Exception as exception:
        err_exit(exception, "Unexpected error in generate_ast_map.")


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])


def detect_matching_declarations(file_a, file_c):
    try:
        generate_ast_map(Definitions.Pa.path + file_a, Definitions.Pc.path + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")

    ast_map = dict()

    try:
        with open("output/ast-map", "r", errors="replace") as ast_map_file:
            map_lines = ast_map_file.readlines()
    except Exception as e:
        err_exit(e, "Unexpected error parsing ast-map in detect_matching declarations")

    match_count = 0
    edit_count = 0
    for line in map_lines:
        line = line.strip()
        if len(line) > 6 and line[:5] == "Match":
            line = clean_parse(line[6:], Definitions.TO)
            if "Decl" not in line[0]:
                continue
            match_count += 1
            ast_map[line[0]] = line[1]
        else:
            edit_count += 1

    with open("output/var-map", "w", errors='replace') as var_map_file:
        for var_a in ast_map.keys():
            var_map_file.write(var_a + " -> " + ast_map[var_a] + "\n")

    return ast_map, match_count, edit_count


def detect_matching_variables(f_a, file_a, f_c, file_c):
    try:
        generate_ast_map(Definitions.Pa.path + file_a, Definitions.Pc.path + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")

    function_a = Definitions.Pa.functions[Definitions.Pa.path + file_a][f_a]
    variable_list_a = function_a.variables.copy()

    while '' in variable_list_a:
        variable_list_a.remove('')

    a_names = [i.split(" ")[-1] for i in variable_list_a]

    function_c = Definitions.Pc.functions[Definitions.Pc.path + file_c][f_c]
    variable_list_c = function_c.variables
    while '' in variable_list_c:
        variable_list_c.remove('')

    # Print.white(variable_list_c)

    json_file_A = Definitions.Pa.path + file_a + ".AST"
    ast_A = Parser.AST_from_file(json_file_A)
    json_file_C = Definitions.Pc.path + file_c + ".AST"
    ast_C = Parser.AST_from_file(json_file_C)

    ast_map = dict()
    try:
        with open("output/ast-map", "r", errors='replace') as ast_map_file:

            map_line = ast_map_file.readline().strip()
            while map_line:
                nodeA, nodeC = clean_parse(map_line, Definitions.TO)

                var_a = id_from_string(nodeA)
                var_a = ast_A[var_a].value_calc(Definitions.Pa.path + file_a)

                var_c = id_from_string(nodeC)
                var_c = ast_C[var_c].value_calc(Definitions.Pc.path + file_c)

                if var_a in a_names:
                    if var_a not in ast_map.keys():
                        ast_map[var_a] = dict()
                    if var_c in ast_map[var_a].keys():
                        ast_map[var_a][var_c] += 1
                    else:
                        ast_map[var_a][var_c] = 1
                map_line = ast_map_file.readline().strip()
    except Exception as e:
        err_exit(e, "Unexpected error while parsing ast-map")

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
        err_exit(e, "Unexpected error while mapping vars.")

    with open("output/var-map", "w", errors='replace') as var_map_file:
        for var_a in variable_mapping.keys():
            var_map_file.write(var_a + " -> " + variable_mapping[var_a] + "\n")

    return variable_mapping


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
