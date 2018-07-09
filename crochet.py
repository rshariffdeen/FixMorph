#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 10:25:58 2018

@author: pedrobw
"""

import time
from Utils import exec_com, err_exit, find_files, clean, get_extensions
import Project
import Print
import ASTVector
import ASTgen
import ASTparser

Pa = None
Pb = None
Pc = None
start = -1

def initialize():
    global Pa, Pb, Pc
    with open('crochet.conf', 'r', errors='replace') as file:
        args = [i.strip() for i in file.readlines()]
    if (len(args) < 3):
        err_exit("Insufficient arguments: Pa, Pb, Pc source paths required.",
                 "Try running:", "\tpython3 ASTcrochet.py $Pa $Pb $Pc")
    Pa = Project.Project(args[0], "Pa")
    Pb = Project.Project(args[1], "Pb")
    Pc = Project.Project(args[2], "Pc")
    clean()


def find_diff_files():
    global Pa, Pb
    extensions = get_extensions(Pa.path, "output/files1")
    extensions = extensions.union(get_extensions(Pb.path, "output/files2"))
    with open('output/exclude_pats', 'w', errors='replace') as exclusions:
        for pattern in extensions:
            exclusions.write(pattern + "\n")
    c = "diff -ENBbwqr " + Pa.path + " " + Pb.path + \
        " -X output/exclude_pats | grep -P '\.c and ' > output/diff"
    exec_com(c, False)

    
def gen_diff():
    # TODO: Include cases where a file is added or removed
    global Pa, Pb
    nums = "0123456789"
    Print.blue("Finding differing files...")
    find_diff_files()
    
    Print.blue("Starting fine-grained diff...\n")
    with open('output/diff', 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            c = "diff -ENBbwr " + file_a + " " + file_b + " > output/file_diff"
            exec_com(c, False)
            pertinent_lines = []
            pertinent_lines_b = []
            with open('output/file_diff', 'r', errors='replace') as file_diff:
                file_line = file_diff.readline().strip()
                while file_line:
                    # In file_diff, line starts with a number, <, >, or -.
                    if file_line[0] in nums:
                        # change (delete + add)
                        if 'c' in file_line:
                            l = file_line.split('c')
                        elif 'd' in file_line:
                            l = file_line.split('d')
                        elif 'a' in file_line:
                            l = file_line.split('a')
                        # range for file_a
                        a = l[0].split(',')
                        start_a = int(a[0])
                        end_a = int(a[-1])
                        # range for file_b
                        b = l[1].split(',')
                        start_b = int(b[0])
                        end_b = int(b[-1])
                        # Pertinent lines in file_a
                        pertinent_lines.append((start_a, end_a))
                        pertinent_lines_b.append((start_b, end_b))
                    file_line = file_diff.readline().strip()
            try:
                Print.blue("\tProject Pa...")
                ASTgen.find_affected_funcs(Pa, file_a, pertinent_lines)
                Print.blue("")
                Print.blue("\tProject Pb...")
                ASTgen.find_affected_funcs(Pb, file_b, pertinent_lines_b)
            except Exception as e:
                err_exit(e, "HERE")
                        
            diff_line = diff.readline().strip()
    
    
def gen_ASTs():
    # Generates an AST file for each .c file
    find_files(Pc.path, "*.c", "output/Cfiles")
    with open("output/Cfiles", 'r', errors='replace') as files:
        file = files.readline().strip()
        while file:
            # Parses it to remove useless information (for us) and gen vects
            try:
                ASTgen.parseAST(file, Pc)
            except Exception as e:
                err_exit(e, "Unexpected error in parseAST with file:", file)
            file = files.readline().strip()

    
def get_vector_list(proj):
    Print.blue("Getting vectors for " + proj.name + "...")
    filepath = "output/vectors_" + proj.name
    find_files(proj.path, "*.vec",  filepath)
    with open(filepath, "r", errors='replace') as file:
        files = [vec.strip() for vec in file.readlines()]
    vecs = []
    for i in range(len(files)):
        with open(files[i], 'r', errors='replace') as vec:
            fl = vec.readline()
            if fl:
                v = [int(s) for s in vec.readline().strip().split(" ")]
                v = ASTVector.ASTVector.normed(v)
                vecs.append((files[i],v))
    return vecs
                
    
def compare():
    global Pa, Pc
    vecs_A = get_vector_list(Pa)
    vecs_C = get_vector_list(Pc)
    
    Print.blue("Variable mapping...\n")
    to_patch = []
    
    UNKNOWN = "#UNKNOWN#"
    factor = 2
    
    for i in vecs_A:
        best = vecs_C[0]
        best_d = ASTVector.ASTVector.dist(i[1], best[1])
        
        # Get best match candidate
        for j in vecs_C:
            d = ASTVector.ASTVector.dist(i[1],j[1])
            if d < best_d:
                best = j
                best_d = d
        
        # Get all pertinent matches (at dist d' < k*best_d) (with k=2?)
        candidates = [best]
        candidates_d = [best_d]
        for j in vecs_C:
            # TODO: Inefficient, computing twice. Should store somewhere?
            d = ASTVector.ASTVector.dist(i[1],j[1])
            if d <= factor*best_d:
                candidates.append(j)
                candidates_d.append(d)
                
        count_unknown = [0 for i in candidates]
        count_vars = [0 for i in candidates]
        var_maps = []
        
        # We go up to -4 to remove the ".vec" part
        fa = i[0].replace(Pa.path, "")[:-4].split(".")
        f_a = fa[-1]
        file_a = ".".join(fa[:-1])
        
        for k in range(len(candidates)):
            candidate = candidates[k]
            fc = candidate[0].replace(Pc.path, "")[:-4].split(".")
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
        best_prop = 1
        var_map = var_maps[0]
        for k in range(1, len(count_unknown)):
            if count_vars[k] > 0:
                if count_unknown[k] < best_count:
                    best_count = count_unknown[k]
                    best = candidates[k]
                    best_d = candidates_d[k]
                    best_prop = count_unknown[k]/count_vars[k]
                    var_map = var_maps[k]
                elif count_unknown[k] == best_count:
                    prop = count_unknown[k]/count_vars[k]
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
        
        fc = best[0].replace(Pc.path, "")[:-4].split(".")
        f_c = fc[-1]
        file_c = ".".join(fc[:-1])
        d_c = str(best_d)
        Print.green("\t\tBest match for " + f_a + " in $Pa/" + file_a + ":")
        Print.blue("\t\tFunction: " + f_c + " in $Pc/" + file_c)
        Print.blue("\t\tDistance: " + d_c + "\n")
                
        to_patch.append((Pa.funcs[Pa.path + file_a][f_a],
                         Pc.funcs[Pc.path + file_c][f_c], var_map))
    return to_patch
    
def path_exception():
    m = "ValueError Exception: Incorrect directory path"
    return ValueError(m)    
    
    
def longestSubstringFinder(string1, string2):
    answer = ""
    maxlen = min(len(string1), len(string2))
    i = 0
    while i < maxlen:
        if string1[i] != string2[i]:
            break
        answer += string1[i]
        i += 1
    return answer
    
def generate_ast_map(source_a, source_b):
    c = "tools/clang-diff/clang-diff -dump-matches " + source_a + " " + \
        source_b + " 2>> errors_clang_diff " \
        "| grep -P '^Match (ParmVar|Var)?Decl(RefExpr)?: '" + \
        " > output/ast-map"
    try:
        exec_com(c, False)
    except Exception as e:
        err_exit(e, "Unexpected error in generate_ast_map.")

def detect_matching_variables(f_a, file_a, f_c, file_c):
    
    generate_ast_map(Pa.path + "/" + file_a, Pc.path + "/" + file_c)
    
    
    function_a = Pa.funcs[Pa.path + file_a][f_a]
    variable_list_a = function_a.variables + function_a.params
    while '' in variable_list_a:
        variable_list_a.remove('')
        
    #Print.white(variable_list_a)
    
    a_names = [i.split(" ")[-1] for i in variable_list_a]
        
    function_c = Pc.funcs[Pc.path + file_c][f_c]
    variable_list_c = function_c.variables + function_c.params
    while '' in variable_list_c:
        variable_list_c.remove('')
    
    #Print.white(variable_list_c)
    
    ast_map = dict()
    try:
        with open("output/ast-map", "r", errors='replace') as ast_map_file:
            map_line = ast_map_file.readline().strip()
            while map_line:
                nodeA, nodeB = clean_parse(map_line, " to ")
                var_a = nodeA.split(": ")[1].split("(")
                #type_a = var_a[1].split(")")[0]
                var_a = var_a[0] #type_a + " " + var_a[0]
                var_c = nodeB.split(": ")[1].split("(")
                #type_c = var_c[1].split(")")[0]
                var_c = var_c[0] #type_c + " " + var_c[0]
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
        err_exit(e, "Unexpected error while matching vars.")

    try:
        with open("output/var-map", "w", errors='replace') as var_map_file:
            for var_a in variable_mapping.keys():
                var_map_file.write(var_a + " -> " + variable_mapping[var_a] + \
                                   "\n")
    except Exception as e:
        err_exit(e, "ASdasdas")
    
    return variable_mapping
    

def gen_func_file(ast_vec_func, output_file):
    start = ast_vec_func.start
    end = ast_vec_func.end
    Print.blue("\t\tStart line: " + str(start))
    Print.blue("\t\tEnd line: " + str(end))
    
    with open(output_file, 'w') as temp:
        with open(ast_vec_func.file, 'r', errors='replace') as file:
            ls = file.readlines()
            # FIXME: This thing isn't copying the function properly sometimes
            if "}" in ls[start] or "#" in ls [start] or ";" in ls[start] or \
                     "/" in ls[start]:
                start += 1
            while start > 0:
                j = start-1
                if len(ls[j].strip()) == 0:
                    break
                elif "}" in ls[j] or "#" in ls [j] or ";" in ls[j] or \
                     "/" in ls[j]:
                    start += 1
                    break
                start = j
            temp.write("".join(ls[start:end]))
            

def gen_temp_files(vec_f, proj, ASTlists):
    Print.blue("\tFunction " + vec_f.function + " in " + proj.name + "...")
    temp_file = "output/temp_" + proj.name + ".c"
    gen_func_file(vec_f, temp_file)
    Print.blue("\t\tClang AST parse " + vec_f.function + " in " + proj.name + "...")
    json_file = "output/json_" + proj.name
    c = "tools/clang-diff/clang-diff -ast-dump-json " + temp_file + " > " + \
        json_file + " 2>> errors_AST_dump"
    exec_com(c, False)
    ASTlists[proj.name] = ASTparser.AST_from_file(json_file)
    
def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content)-1:
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
    half = len(nodes)//2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]
    

def ASTdump(file, output):
    c = "tools/clang-diff/clang-diff -s 2147483647 -ast-dump-json " + file + \
        " 2>> output/errors_clang_diff > " + output
    exec_com(c)
    

def ASTscript(file1, file2, output, only_matches=False):
    c = "tools/clang-diff/clang-diff -s 2147483647 -dump-matches " + file1 + \
        " " + file2 + " 2>> output/errors_clang_diff "
    if only_matches:
        c += "| grep '^Match ' "
    c += " > " + output
    exec_com(c)
    
    
def transplantation(to_patch):
    
    UPDATE = "Update"
    MOVE = "Move"
    INSERT = "Insert"
    DELETE = "Delete"
    MATCH = "Match"
    TO = " to "
    AT = " at "
    INTO = " into "
    
    for (vec_f_a, vec_f_c, var_map) in to_patch:
        try:
            vec_f_b_file = vec_f_a.file.replace(Pa.path, Pb.path)
            if vec_f_a.function in Pb.funcs[vec_f_b_file].keys():
                vec_f_b = Pb.funcs[vec_f_b_file][vec_f_a.function]
            else:
                err_exit(vec_f_a.function, vec_f_b_file, Pb.funcs[vec_f_b_file].keys())
            ASTlists = dict()
        except Exception as e:
            err_exit(e, vec_f_b_file, vec_f_a, Pa.path, Pb.path, vec_f_a.function)
        
        Print.blue("Generating temp files for each pertinent function...")
        
        try:
            gen_temp_files(vec_f_a, Pa, ASTlists)
            gen_temp_files(vec_f_b, Pb, ASTlists)
            gen_temp_files(vec_f_c, Pc, ASTlists)
        except:
            err_exit("!!")
        
        Print.blue("Generating edit script: " + Pa.name + TO + Pb.name + "...")
        
        try:
            ASTscript(vec_f_a.file, vec_f_b_file, "output/diff_script_AB")
            Print.blue("Finding common structures in " + Pa.name + \
                       " with respect to " + Pb.name + "...")
            ASTscript(vec_f_a.file, vec_f_c.file, "output/diff_script_AC")
        except:
            err_exit("!!!")
                      
        Print.blue("Generating edit script: " + Pc.name + TO + "Pd...")

        instruction_AB = list()
        match_BA = dict()
        with open('output/diff_script_AB', 'r', errors='replace') as script_AB:
            line = script_AB.readline().strip()
            while line:
                line = line.split(" ")
                instruction = line[0]
                content = " ".join(line[1:])
                # Match nodeA to nodeB
                if instruction == MATCH:
                    try:
                        nodeA, nodeB = clean_parse(content, TO)
                        match_BA[nodeB] = nodeA
                    except Exception as e:
                        err_exit(e, "Something went wrong in MATCH (AB).",
                                 line, instruction, content)
                # Update nodeA to label
                elif instruction == UPDATE:
                    try:
                        nodeA, label = clean_parse(content, TO)
                        instruction_AB.append((instruction, nodeA, label))
                    except Exception as e:
                        err_exit(e, "Something went wrong in UPDATE.")
                # Delete nodeA
                elif instruction == DELETE:
                    try:
                        nodeA = content
                        instruction_AB.append((instruction, nodeA))
                    except Exception as e:
                        err_exit(e, "Something went wrong in DELETE.")
                # Move nodeA into nodeB at pos
                elif instruction == MOVE:
                    try:
                        nodeA, nodeB = clean_parse(content, INTO)
                        nodeB_at = nodeB.split(AT)
                        nodeB = AT.join(nodeB_at[:-1])
                        pos = nodeB_at[-1]
                        instruction_AB.append((instruction, nodeA, nodeB, pos))
                    except Exception as e:
                        err_exit(e, "Something went wrong in DELETE.")
                # Insert nodeB1 into nodeB2 at pos
                elif instruction == INSERT:
                    try:
                        nodeB1, nodeB2 = clean_parse(content, INTO)
                        nodeB2_at = nodeB2.split(AT)
                        nodeB2 = AT.join(nodeB2_at[:-1])
                        pos = nodeB2_at[-1]
                        instruction_AB.append((instruction, nodeB1, nodeB2,
                                              pos))
                    except Exception as e:
                        err_exit(e, "Something went wrong in INSERT.")
                line = script_AB.readline().strip()
                
        match_AC = dict()
        with open('output/diff_script_AC', 'r', errors='replace') as script_AC:
            line = script_AC.readline().strip()
            while line:
                line = line.split(" ")
                instruction = line[0]
                content = " ".join(line[1:])
                if instruction == MATCH:
                    try:
                        nodeA, nodeC = clean_parse(content, TO)
                        match_AC[nodeA] = nodeC
                    except Exception as e:
                        err_exit(e, "Something went wrong in MATCH (AC).",
                                 line, instruction, content)
                line = script_AC.readline().strip()
        
        instruction_CD = list()
        for i in instruction_AB:
            instruction = i[0]
            # Update nodeA to label -> Update nodeC to label
            if instruction == UPDATE:
                try:
                    nodeA = i[1]
                    label = i[2]
                    nodeC = "?"
                    if nodeA in match_AC.keys():
                        nodeC = match_AC[nodeA]
                        #nodeC = nodeC.split("(")[-1][:-1]
                        #nodeC = ASTlists[Pc.name][int(nodeC)]
                    # TODO: else?
                    instruction_CD.append((UPDATE, nodeC, label))
                except Exception as e:
                    err_exit(e, "Something went wrong with UPDATE.")
                #print(UPDATE + " " + str(nodeC) + TO + label)
            # Delete nodeA -> Delete nodeC
            elif instruction == DELETE:
                try:
                    nodeA = i[1]
                    nodeC = "?"
                    if nodeA in match_AC.keys():
                        nodeC = match_AC[nodeA]
                        #nodeC = nodeC.split("(")[-1][:-1]
                        #nodeC = ASTlists[Pc.name][int(nodeC)]
                    # TODO: else?
                    instruction_CD.append((DELETE, nodeC))
                except Exception as e:
                    err_exit(e, "Something went wrong with DELETE.")
                #print(DELETE + " " + str(nodeC))
            # Move nodeA to nodeB at pos -> Move nodeC to nodeD at pos
            elif instruction == MOVE:
                try:
                    nodeA = i[1]
                    nodeB = i[2]
                    pos = int(i[3])
                    nodeC = "?"
                    nodeD = nodeB
                    #if "(" in nodeD:
                    #    nodeD = nodeD.split("(")[-1][:-1]
                    #    nodeD = ASTlists[Pb.name][int(nodeD)]
                    if nodeA in match_AC.keys():
                        nodeC = match_AC[nodeA]
                        #if "(" in nodeC:
                        #    nodeC = nodeC.split("(")[-1][:-1]
                        #    nodeC = ASTlists[Pc.name][int(nodeC)]
                        if nodeB in match_BA.keys():
                            nodeA2 = match_BA[nodeB]
                            if nodeA2 in match_AC.keys():
                                nodeD = match_AC[nodeA2]
                                #if "(" in nodeD:
                                #    nodeD = nodeD.split("(")[-1][:-1]
                                #    nodeD = ASTlists[Pc.name][int(nodeD)]
                                try:    
                                    m = 0
                                    M = len(nodeB.children)
                                    if pos != 0 and pos < M-1:
                                        nodeB_l = nodeB.children[pos-1]
                                        nodeB_r = nodeB.children[pos+1]
                                        if nodeB_l in match_BA.keys():
                                            nodeA_l = match_BA[nodeB_l]
                                            if nodeA_l in match_AC.keys():
                                                nodeC_l = match_AC[nodeA_l]
                                                if nodeC_l in nodeD.children:
                                                    m = nodeD.children.index(nodeC_l)
                                                    pos = m+1
                                        elif nodeB_r in match_BA.keys():
                                            nodeA_r = match_BA[nodeB_r]
                                            if nodeA_r in match_AC.keys():
                                                nodeC_r = match_AC[nodeA_r]
                                                if nodeC_r in nodeD.children:
                                                    M = nodeD.children.index(nodeC_r)
                                                    pos = M-1
                                    elif pos >= M - 1:
                                        pos += len(nodeD.children) - M - 1
                                except Exception as e:
                                    err_exit(e, "HERE1")
                                            
                    # TODO: else?
                    instruction_CD.append((MOVE, nodeC, nodeD, pos))
                except Exception as e:
                    err_exit(e, "Something went wrong with MOVE.")
                #print(MOVE + " " + str(nodeC) + INTO + str(nodeD) + AT + pos)
            # Insert nodeB1 to nodeB2 at pos -> Insert nodeD1 to nodeD2 at pos
            elif instruction == INSERT:
                try:
                    nodeB1 = i[1]
                    nodeB2 = i[2]
                    pos = int(i[3])
                    nodeD1 = nodeB1
                    #if "(" in nodeD1:
                    #    nodeD1 = nodeD1.split("(")[-1][:-1]
                    #    nodeD1 = ASTlists[Pb.name][int(nodeD1)]
                    nodeD2 = nodeB2
                    #if "(" in nodeD2:
                    #    nodeD2 = nodeD2.split("(")[-1][:-1]
                    #    nodeD2 = ASTlists[Pb.name][int(nodeD2)]
                    if nodeB1 in match_BA.keys():
                        nodeA1 = match_BA[nodeB1]
                        if nodeA1 in match_AC.keys():
                            nodeD1 = match_AC[nodeA1]
                            #if "(" in nodeD1:
                            #    nodeD1 = nodeD1.split("(")[-1][:-1]
                            #    nodeD1 = ASTlists[Pc.name][int(nodeD1)]
                    if nodeB2 in match_BA.keys():
                        nodeA2 = match_BA[nodeB2]
                        if nodeA2 in match_AC.keys():
                            nodeD2 = match_AC[nodeA2]
                            #if "(" in nodeD2:
                            #    nodeD2 = nodeD2.split("(")[-1][:-1]
                            #    nodeD2 = ASTlists[Pc.name][int(nodeD2)]
                            '''try:
                                m = 0
                                true_B2 = nodeB2
                                #if "(" in nodeB2:
                                #    true_B2 = nodeB2.split("(")[-1][:-1]
                                #    true_B2 = ASTlists[Pb.name][int(true_B2)]
                                M = len(true_B2.children)
                                if pos != 0 and pos < M-1:
                                    nodeB2_l = true_B2.children[pos-1]
                                    nodeB2_r = true_B2.children[pos+1]
                                    if nodeB2_l in match_BA.keys():
                                        nodeA2_l = match_BA[nodeB2_l]
                                        if nodeA2_l in match_AC.keys():
                                            nodeD2_l = match_AC[nodeA2_l]
                                            if nodeD2_l in nodeD2.children:
                                                m = nodeD2.children.index(nodeD2_l)
                                                pos = m+1
                                    elif nodeB2_r in match_BA.keys():
                                        nodeA2_r = match_BA[nodeB2_r]
                                        if nodeA2_r in match_AC.keys():
                                            nodeD2_r = match_AC[nodeA2_r]
                                            if nodeD2_r in nodeD2.children:
                                                M = nodeD2.children.index(nodeD2_r)
                                                pos = max(0, M-1)
                                elif pos >= M - 1:
                                    pos += len(nodeD2.children) - M - 1
                            except Exception as e:
                                err_exit(e, "Here2")'''
                    instruction_CD.append((INSERT, nodeD1, nodeD2, pos))
                except Exception as e:
                    err_exit(e, "Something went wrong with INSERT.")
                #print(INSERT + " " + str(nodeD1) + INTO + str(nodeD2) + AT + \
                #      pos)
        Print.white("Proposed patch from Pc to Pd")
        for i in instruction_CD:
            Print.white("\t" + " ".join([str(j) for j in i]))
        
        Print.white("Original patch from Pa to Pb")
        for i in instruction_AB:
            Print.white("\t" + " ".join([str(j) for j in i]))
            

def safe_exec(function, title, *args):
    Print.title("Starting " + title + "...")
    descr = title[0].lower() + title[1:]
    try:
        if not args:
            a = function()
        else:
            a = function(*args)
        runtime = str(time.time() - start)
        Print.rose("Successful " + descr + ", after " + runtime + " seconds.")
    except Exception as e:
        runtime = str(time.time() - start)
        Print.red("Crash during " + descr + ", after " + runtime + " seconds.")
        err_exit(e, "Unexpected error during " + descr + ".")
    return a
                    
def run_crochet():
    global Pa, Pb, Pc, start
    # Little crochet introduction
    Print.start()
    
    # Time for final running time
    start = time.time()
    
    # Prepare projects directories by getting paths and cleaning residual files
    safe_exec(initialize, "projects initialization and cleaning")
    
    # Generates vectors for pertinent functions (modified from Pa to Pb)
    safe_exec(gen_diff, "search for affected functions and vector generation")
              
    # Generates vectors for all functions in Pc
    safe_exec(gen_ASTs, "vector generation for functions in Pc")

    # Pairwise vector comparison for matching
    to_patch = safe_exec(compare, "pairwise vector comparison for matching")
    
    # Using all previous structures to transplant patch
    safe_exec(transplantation, "patch transplantation", to_patch)
    
    # Final clean
    Print.title("Cleaning residual files generated by Crochet...")
    
    # Final running time and exit message
    runtime = str(time.time() - start)
    Print.exit_msg(runtime)
    
    
if __name__=="__main__":
    #test_parsing()
    try:
        run_crochet()
    except KeyboardInterrupt as e:
        err_exit("Program Interrupted by User")