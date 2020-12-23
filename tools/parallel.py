import multiprocessing as mp
from common import definitions, values, utilities
from tools import emitter, oracle, extractor, finder, mapper, converter
from typing import List, Dict, Optional
from pysmt.shortcuts import is_sat, Not, And, TRUE
from multiprocessing import TimeoutError
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
import threading
import time
from ast import ast_generator

BREAK_LIST = [",", " ", " _", ";", "\n"]


def collect_result(result):
    global result_list
    result_list.append(result)


def collect_result_timeout(result):
    global result_list, expected_count
    result_list.append(result)
    if len(result_list) == expected_count:
        pool.terminate()


def collect_result_one(result):
    global result_list, found_one
    result_list.append(result)
    if result[0] is True:
        found_one = True
        pool.terminate()


def abortable_worker(func, *args, **kwargs):
    default_value = kwargs.get('default', None)
    index = kwargs.get('index', None)
    p = ThreadPool(1)
    res = p.apply_async(func, args=args)
    try:
        out = res.get(values.DEFAULT_TIMEOUT_SAT)
        return out
    except TimeoutError:
        emitter.warning("\t[warning] timeout raised on a thread")
        return default_value, index


def derive_namespace_map(ast_node_map, source_a, source_c, slice_file_a):
    global pool, result_list, expected_count
    result_list = []

    namespace_map = dict()
    refined_var_map = dict()
    emitter.normal("\tderiving namespace map")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    neighbor_ast = None
    neighbor_ast_range = None
    neighbor_type, neighbor_name, slice = str(slice_file_a).split("/")[-1].split(".c.")[-1].split(".")
    if neighbor_type == "func":
        neighbor_ast = finder.search_function_node_by_name(ast_tree_a, neighbor_name)
    elif neighbor_type == "var":
        neighbor_name = neighbor_name[:neighbor_name.rfind("_")]
        neighbor_ast = finder.search_node(ast_tree_a, "VarDecl", neighbor_name)
    elif neighbor_type == "struct":
        neighbor_ast = finder.search_node(ast_tree_a, "RecordDecl", neighbor_name)

    if neighbor_ast:
        neighbor_ast_range = (int(neighbor_ast['begin']), int(neighbor_ast['end']))
    else:
        utilities.error_exit("No neighbor AST Found")

    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())
    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
        value_score = 1
        if ast_node_a:
            if ast_node_id_a in range(neighbor_ast_range[0], neighbor_ast_range[1]):
                value_score = 100
        # result_list.append(extractor.extract_mapping(ast_node_a, ast_node_c, value_score))
        pool.apply_async(extractor.extract_mapping, args=(ast_node_a, ast_node_c, value_score),
                         callback=collect_result)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for id_a, id_c, score in result_list:
        if id_a is None or id_c is None:
            continue
        if id_a not in namespace_map:
            namespace_map[id_a] = dict()
        if id_c not in namespace_map[id_a]:
            namespace_map[id_a][id_c] = score
        else:
            namespace_map[id_a][id_c] = namespace_map[id_a][id_c] + score

    for value_a in namespace_map:
        candidate_list = namespace_map[value_a]
        max_score = 0
        best_candidate = None
        for candidate in candidate_list:
            candidate_score = candidate_list[candidate]
            if max_score < candidate_score:
                best_candidate = candidate
                max_score = candidate_score
        if "(" in value_a:
            value_a = value_a.split("(")[0] + "("
        if "(" in best_candidate:
            best_candidate = best_candidate.split("(")[0] + "("
        if not value_a or not best_candidate:
            continue
        if any(token in str(value_a).lower() for token in BREAK_LIST):
            continue
        if any(token in str(best_candidate).lower() for token in BREAK_LIST):
            continue

        # generate all possible member relations with each var mapping
        if "." in value_a and "." in best_candidate:
            refined_var_map["." + value_a.split(".")[-1]] = "." + best_candidate.split(".")[-1]
        refined_var_map[value_a] = best_candidate

    return refined_var_map


def get_mapping(map_file_name):
    global pool, result_list, expected_count
    result_list = []
    node_map = dict()
    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    with open(map_file_name, 'r') as ast_map:
        line_list = ast_map.readlines()

    for line in line_list:
        line = line.strip()
        line = line.split(" ")
        operation = line[0]
        content = " ".join(line[1:])
        if operation == definitions.MATCH:
            # result_list.append(utilities.clean_parse(content, definitions.TO))
            pool.apply_async(utilities.clean_parse, args=(content, definitions.TO),
                             callback=collect_result)
            # try:
            #     node_a, node_c = clean_parse(content, definitions.TO)
            #     node_map[node_a] = node_c
            # except Exception as exception:
            #     error_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for node_a, node_c in result_list:
        node_map[node_a] = node_c

    return node_map


# adjust the mapping via anti-unification
def extend_mapping(ast_node_map, source_a, source_c):
    global pool, result_list, expected_count
    result_list = []

    emitter.normal("\tupdating ast map using anti-unification")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    for node_a in ast_node_map:
        node_c = ast_node_map[node_a]
        ast_node_id_a = int(str(node_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(node_c).split("(")[1].split(")")[0])
        ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
        # result_list.append(mapper.anti_unification(ast_node_a, ast_node_c))

        pool.apply_async(mapper.anti_unification, args=(ast_node_a, ast_node_c),
                         callback=collect_result)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for au_pairs in result_list:
        for au_pair_key in au_pairs:
            au_pair_value = au_pairs[au_pair_key]
            if au_pair_key not in ast_node_map:
                ast_node_map[au_pair_key] = au_pair_value

    return ast_node_map


def generate_method_invocation_map(source_a, source_c, method_name):
    global pool, result_list, expected_count
    result_list = []
    method_invocation_map = dict()
    emitter.normal("\tderiving method invocation map")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    map_file_name = definitions.DIRECTORY_OUTPUT + "/" + source_a.split("/")[-1] + ".map"
    mapper.generate_map(source_a, source_c, map_file_name)
    global_ast_node_map = get_mapping(map_file_name)

    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    for ast_node_txt_a in global_ast_node_map:
        ast_node_txt_c = global_ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        node_type_a = str(ast_node_txt_c).split("(")[0].split(" ")[-1]
        node_type_c = str(ast_node_txt_c).split("(")[0].split(" ")[-1]
        if node_type_a in ["CallExpr"] and node_type_c in ["CallExpr"]:
            ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
            ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
            children_a = ast_node_a["children"]
            children_c = ast_node_c["children"]
            if len(children_a) < 1 or len(children_c) < 1:
                continue
            if method_name == children_a[0]["value"]:
                result_list.append(extractor.extract_method_invocations(global_ast_node_map, ast_node_a, ast_node_c, method_name))
                # pool.apply_async(extractor.extract_method_invocations, args=(ast_node_a, ast_node_c, ast_node_map),
                #                  callback=collect_result)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for method_name_a, method_name_c, arg_operation in result_list:
        if method_name_a is not None:
            if method_name_a not in method_invocation_map:
                method_invocation_map[method_name_a] = dict()
            mappings = method_invocation_map[method_name_a]
            if method_name_c not in mappings:
                mappings[method_name_c] = (1, arg_operation)
            else:
                mappings[method_name_c][0] = mappings[method_name_c][0]  + 1
            method_invocation_map[method_name_a] = mappings
    return method_invocation_map


def generate_function_signature_map(ast_node_map, source_a, source_c):
    function_map = dict()
    emitter.normal("\tderiving function signature map")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())
    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
        pool.apply_async(extractor.extract_method_signatures, args=(ast_node_a, ast_node_c, ast_node_map),
                         callback=collect_result)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for method_name, arg_operation in result_list:
        if method_name is not None:
            function_map[method_name] = arg_operation

    return function_map

