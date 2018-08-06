#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import time
from Utils import exec_com, err_exit, find_files, clean, get_extensions
import Print
import Common
import ASTVector
import ASTgen
import ASTparser

excluded_extensions_pa = "output/excluded-extensions-pa"
excluded_extensions_pb = "output/excluded-extensions-pb"
excluded_extensions = 'output/excluded-extensions'


def find_diff_files():
    extensions = get_extensions(Common.Pa.path, excluded_extensions_pa)
    extensions = extensions.union(get_extensions(Common.Pb.path, excluded_extensions_pb))
    with open(excluded_extensions, 'w', errors='replace') as exclusions:
        for pattern in extensions:
            exclusions.write(pattern + "\n")
    # TODO: Include cases where a file is added or removed
    c = "diff -ENZBbwqr " + Common.Pa.path + " " + Common.Pb.path + " -X " + excluded_extensions + "> output/diff; "
    c += "cat output/diff | grep -P '\.c and ' > output/diff_C; "
    c += "cat output/diff | grep -P '\.h and ' > output/diff_H; "
    exec_com(c, False)


def generate_diff():
    # .h and .c files
    Print.blue("Finding differing files...")
    find_diff_files()

    # H files
    with open('output/diff_H', 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            ASTgen.llvm_format(file_a)
            ASTgen.llvm_format(file_b)
            ASTgen.parseAST(file_a, Pa, use_deckard=True, is_header=True)
            Print.success("\t\tFile successfully found: " + file_a.split("/")[-1] + " from " + Common.Pa.name + " to " + Common.Pb.name)
            diff_line = diff.readline().strip()

    # C files
    Print.blue("Starting fine-grained diff...\n")
    with open('output/diff_C', 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            ASTgen.llvm_format(file_a)
            ASTgen.llvm_format(file_b)
            diff_command = "diff -ENBZbwr " + file_a + " " + file_b + " > output/C_diff"
            exec_com(diff_command)
            pertinent_lines_a = []
            pertinent_lines_b = []
            with open('output/C_diff', 'r', errors='replace') as file_diff:
                file_line = file_diff.readline().strip()
                while file_line:
                    # We only want lines starting with a line number
                    if 48 <= ord(file_line[0]) <= 57:
                        # add
                        if 'a' in file_line:
                            l = file_line.split('a')
                        # delete
                        elif 'd' in file_line:
                            l = file_line.split('d')
                        # change (delete + add)
                        elif 'c' in file_line:
                            l = file_line.split('c')
                        # range for file_a
                        a = l[0].split(',')
                        start_a = int(a[0])
                        end_a = int(a[-1])
                        # range for file_b
                        b = l[1].split(',')
                        start_b = int(b[0])
                        end_b = int(b[-1])
                        # Pertinent lines in file_a
                        pertinent_lines_a.append((start_a, end_a))
                        pertinent_lines_b.append((start_b, end_b))
                    file_line = file_diff.readline().strip()
            try:
                ASTgen.find_affected_funcs(Common.Pa, file_a, pertinent_lines_a)
                ASTgen.find_affected_funcs(Common.Pb, file_b, pertinent_lines_b)
            except Exception as e:
                err_exit(e, "Failed at finding affected functions.")

            diff_line = diff.readline().strip()


def generate_vector_for_extension(file_extension, output, is_header=False):

    Print.blue("Generate vectors for " + file_extension + " files in " + Common.Pc.name + "...")
    # Generates an AST file for each file of extension ext
    find_files(Common.Pc.path, file_extension, output)
    with open(output, 'r', errors='replace') as file_list:
        file_name = file_list.readline().strip()
        while file_name:
            # Parses it to get useful information and generate vectors
            try:
                ASTgen.parseAST(file_name, Common.Pc, use_deckard=True, is_header=is_header)
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

    Print.blue("Getting vectors for " + rxt + " files in " + project.name + "...")
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
                v = ASTVector.ASTVector.normed(v)
                vecs.append((files[i], v))
    return vecs


def clone_detection_header_files():
    extension = "*\.h\.vec"
    candidate_list = []
    vector_list_a = get_vector_list(Common.Pa, extension)
    if len(vector_list_a) == 0:
        return candidate_list
    vector_list_c = get_vector_list(Common.Pc, extension)
    factor = 2

    Print.blue("Declaration mapping for *.h files")
    for i in vector_list_a:
        best = vector_list_c[0]
        best_d = ASTVector.ASTVector.dist(i[1], best[1])
        dist = dict()

        for j in vector_list_c:
            d = ASTVector.ASTVector.dist(i[1], best[1])
            dist[j[0]] = d
            if d < best_d:
                best = j
                best_d = d

        candidates = [best]
        candidates_d = [best_d]
        for j in vector_list_c:
            if j != best:
                d = dist[j[0]]
                if d <= factor * best_d:
                    candidates.append(j)
                    candidates_d.append(d)

        decl_maps = list()
        match_score = list()
        matches = list()

        file_a = i[0].replace(Common.Pa.path, "")[:-4]
        for k in range(len(candidates)):
            candidate = candidates[k]
            file_c = candidate[0].replace(Pc.path, "")[:-4]
            d_c = str(candidates_d[k])
            Print.blue("\tPossible match for " + file_a + " in Pa:")
            Print.blue("\t\tFile: " + file_c + " in Pc")
            Print.blue("\t\tDistance: " + d_c + "\n")
            Print.blue("\tDeclaration mapping from " + file_a + " to " + \
                       file_c + ":")
            try:
                decl_map, match, edit = detect_matching_declarations(file_a, file_c)
                decl_maps.append(decl_map)
                match_score.append((match - edit) / (match + edit))
                matches.append(match)
            except Exception as e:
                err_exit(e, "Unexpected error while matching declarations.")
            with open('output/var-map', 'r', errors='replace') as mapped:
                mapping = mapped.readline().strip()
                while mapping:
                    Print.grey("\t\t" + mapping)
                    mapping = mapped.readline().strip()

        best_score = match_score[0]
        best = candidates[0]
        best_d = candidates_d[0]
        best_match = matches[0]
        best_index = [k]

        for k in range(1, len(candidates)):
            score = match_score[k]
            d = candidates_d[k]
            match = matches[k]
            if score > best_score:
                best_score = score
                best_index = [k]
            elif score == best_score:
                if d < best_d:
                    best_d = d
                    best_index = [k]
                elif d == best_d:
                    if match > best_match:
                        best_match = match
                        best_index = [k]
                    else:
                        best_index.append(k)
        # Potentially many identical matches
        M = len(best_index)
        m = min(1, M)
        Print.success("\t" + str(M) + " match" + "es" * m + " for " + file_a)
        for index in best_index:
            file_c = candidates[index][0][:-4].replace(Pc.path, "")
            d_c = str(candidates_d[index])
            decl_map = decl_maps[index]
            Print.success("\t\tMatch for " + file_a + " in Pa:")
            Print.blue("\t\tFile: " + file_c + " in Pc.")
            Print.blue("\t\tDistance: " + d_c + ".\n")
            # Print.green((Common.Pa.path + file_a, Pc.path + file_c, var_map))
            candidate_list.append((Common.Pa.path + file_a, Pc.path + file_c, decl_map))
    return candidate_list


def clone_detection_for_c_files():

    c_ext = "*\.c\.*\.vec"
    vector_list_A = get_vector_list(Common.Pa, c_ext)
    vector_list_C = get_vector_list(Common.Pc, c_ext)

    Print.blue("Variable mapping...\n")
    to_patch = []

    UNKNOWN = "#UNKNOWN#"
    factor = 2

    for i in vector_list_A:
        best = vector_list_C[0]
        best_d = ASTVector.ASTVector.dist(i[1], best[1])
        dist = dict()

        # Get best match candidate
        for j in vector_list_C:
            d = ASTVector.ASTVector.dist(i[1], j[1])
            dist[j[0]] = d
            if d < best_d:
                best = j
                best_d = d

        # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
        candidates = [best]
        candidates_d = [best_d]
        for j in vector_list_C:
            if j != best:
                d = dist[j[0]]
                if d <= factor * best_d:
                    candidates.append(j)
                    candidates_d.append(d)

        count_unknown = [0] * len(candidates)
        count_vars = [0] * len(candidates)
        var_maps = []

        # We go up to -4 to remove the ".vec" part [filepath.function.vec]
        fa = i[0].replace(Common.Pa.path, "")[:-4].split(".")
        f_a = fa[-1]
        file_a = ".".join(fa[:-1])

        # TODO: Correct once I have appropriate only function comparison
        for k in range(len(candidates)):
            candidate = candidates[k]
            fc = candidate[0].replace(Common.Pc.path, "")[:-4].split(".")
            f_c = fc[-1]
            file_c = ".".join(fc[:-1])
            d_c = str(candidates_d[k])
            Print.blue("\tPossible match for " + f_a + " in $Pa/" + file_a + \
                       ":")
            Print.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
            Print.blue("\t\tDistance: " + d_c + "\n")
            Print.blue("\tVariable mapping from " + f_a + " to " + f_c + ":")
            try:
                var_map = detect_matching_variables(f_a, file_a, f_c, file_c)
                var_maps.append(var_map)
            except Exception as e:
                err_exit(e, "Unexpected error while matching variables.")
            with open('output/var-map', 'r', errors='replace') as mapped:
                mapping = mapped.readline().strip()
                while mapping:
                    Print.grey("\t\t" + mapping)
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

        fc = best[0].replace(Common.Pc.path, "")[:-4].split(".")
        f_c = fc[-1]
        file_c = ".".join(fc[:-1])
        d_c = str(best_d)
        Print.success("\t\tBest match for " + f_a + " in $Pa/" + file_a + ":")
        Print.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
        Print.blue("\t\tDistance: " + d_c + "\n")

        to_patch.append((Common.Pa.functions[Common.Pa.path + file_a][f_a],
                         Common.Pc.functions[Common.Pc.path + file_c][f_c], var_map))
    return to_patch


def generate_ast_map(source_a, source_b):
    c = Common.DIFF_COMMAND + "-dump-matches " + source_a + " " + source_b
    if source_a[-1] == "h":
        c += " --"
    c += " 2>> output/errors_clang_diff"
    c += "| grep -P '^Match ' | grep -P '^Match ' > output/ast-map"
    try:
        exec_com(c, True)
    except Exception as e:
        err_exit(e, "Unexpected error in generate_ast_map.")


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])




def detect_matching_declarations(file_a, file_c):
    try:
        generate_ast_map(Common.Pa.path + file_a, Common.Pc.path + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")

    ast_map = dict()

    try:
        with open("output/ast-map", "r", errors="replace") as ast_map_file:
            map_lines = ast_map_file.readlines()
    except Exception as e:
        err_exit(e, "Unexpected error parsing ast-map in detect_matching declarations")

    matches = 0
    edits = 0
    for line in map_lines:
        line = line.strip()
        if len(line) > 6 and line[:5] == "Match":
            line = clean_parse(line[6:], Common.TO)
            if "Decl" not in line[0]:
                continue
            matches += 1
            ast_map[line[0]] = line[1]
        else:
            edits += 1

    with open("output/var-map", "w", errors='replace') as var_map_file:
        for var_a in ast_map.keys():
            var_map_file.write(var_a + " -> " + ast_map[var_a] + "\n")

    return ast_map, matches, edits


def detect_matching_variables(f_a, file_a, f_c, file_c):
    try:
        generate_ast_map(Common.Pa.path + file_a, Common.Pc.path + file_c)
    except Exception as e:
        err_exit(e, "Error at generate_ast_map.")

    function_a = Common.Pa.functions[Common.Pa.path + file_a][f_a]
    variable_list_a = function_a.variables.copy()

    while '' in variable_list_a:
        variable_list_a.remove('')

    a_names = [i.split(" ")[-1] for i in variable_list_a]

    function_c = Common.Pc.functions[Common.Pc.path + file_c][f_c]
    variable_list_c = function_c.variables
    while '' in variable_list_c:
        variable_list_c.remove('')

    # Print.white(variable_list_c)

    json_file_A = Common.Pa.path + file_a + ".AST"
    ast_A = ASTparser.AST_from_file(json_file_A)
    json_file_C = Common.Pc.path + file_c + ".AST"
    ast_C = ASTparser.AST_from_file(json_file_C)

    ast_map = dict()
    try:
        with open("output/ast-map", "r", errors='replace') as ast_map_file:

            map_line = ast_map_file.readline().strip()
            while map_line:
                nodeA, nodeC = clean_parse(map_line, Common.TO)

                var_a = id_from_string(nodeA)
                var_a = ast_A[var_a].value_calc(Common.Pa.path + file_a)

                var_c = id_from_string(nodeC)
                var_c = ast_C[var_c].value_calc(Common.Pc.path + file_c)

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


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Print.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Print.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Print.error("Crash during " + description + ", after " + duration + " seconds.")
        err_exit(exception, "Unexpected error during " + description + ".")
    return result


def detect():
    Print.title("Locating vulnerable functions")
    safe_exec(generate_diff, "search for affected functions")
    # Generates vectors for all functions in Pc
    safe_exec(generate_vectors, "vector generation for all functions in Pc")
    # Pairwise vector comparison for matching
    Common.header_file_list_to_patch = safe_exec(clone_detection_header_files, "clone detection for header files")
    Common.c_file_list_to_patch = safe_exec(clone_detection_for_c_files, "clone detection for C files")

