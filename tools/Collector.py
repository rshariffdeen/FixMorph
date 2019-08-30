#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import os
import Emitter
import Logger
import collections


def collect_symbolic_expressions(trace_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\t\tcollecting symbolic expressions")
    var_expr_map = dict()
    if os.path.exists(trace_file_path):
        with open(trace_file_path, 'r') as trace_file:
            for line in trace_file:
                if '[var-expr]' in line:
                    line = line.split("[var-expr] ")[-1]
                    var_name, var_expr = line.split(":")
                    var_expr = var_expr.replace("\n", "")
                    if var_name not in var_expr_map.keys():
                        var_expr_map[var_name] = dict()
                        var_expr_map[var_name]['expr_list'] = list()
                    var_expr_map[var_name]['expr_list'] .append(var_expr)
                if '[var-type]' in line:
                    line = line.split("[var-type]: ")[-1]
                    var_name = line.split(":")[0]
                    var_type = line.split(":")[1]
                    var_type = var_type.replace("\n", "")
                    var_expr_map[var_name]['data_type'] = var_type
    return var_expr_map


def collect_values(trace_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\t\t\tcollecting variable values")
    var_value_map = dict()
    if os.path.exists(trace_file_path):
        with open(trace_file_path, 'r') as trace_file:
            for line in trace_file:
                if '[var-expr]' in line:
                    line = line.split("[var-expr] ")[-1]
                    var_name, var_value = line.split(":")
                    var_value = var_value.replace("\n", "")
                    var_value = var_value.split(" ")[1]
                    if var_name not in var_value_map.keys():
                        var_value_map[var_name] = dict()
                        var_value_map[var_name]['value_list'] = list()
                    var_value_map[var_name]['value_list'].append(var_value)
                if '[var-type]' in line:
                    line = line.split("[var-type]: ")[-1]
                    var_name = line.split(":")[0]
                    var_type = line.split(":")[1]
                    var_type = var_type.replace("\n", "")
                    var_value_map[var_name]['data_type'] = var_type
    return var_value_map


def collect_symbolic_path(file_path, project_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting symbolic path conditions")
    constraints = dict()
    last_sym_path = ""
    if os.path.exists(file_path):
        source_path = ""
        path_condition = ""
        with open(file_path, 'r') as trace_file:
            for line in trace_file:
                if '[path:condition]' in line:
                    if project_path in line:
                        source_path = str(line.replace("[path:condition]", '')).split(" : ")[0]
                        source_path = source_path.strip()
                        source_path = os.path.abspath(source_path)
                        path_condition = str(line.replace("[path:condition]", '')).split(" : ")[1]
                        continue
                if source_path:
                    if "(exit)" not in line:
                        path_condition = path_condition + line
                    else:
                        if source_path not in constraints.keys():
                            constraints[source_path] = list()
                        constraints[source_path].append((path_condition))
                        last_sym_path = path_condition
                        source_path = ""
                        path_condition = ""
    # constraints['last-sym-path'] = last_sym_path
    # print(constraints.keys())
    return constraints, last_sym_path


def collect_trace(file_path, project_path, suspicious_loc_list):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting trace")
    list_trace = list()
    if os.path.exists(file_path):
        with open(file_path, 'r') as trace_file:
            for line in trace_file:
                if '[trace]' in line:
                    if project_path in line:
                        trace_line = str(line.replace("[trace]", '')).split(" - ")[0]
                        trace_line = trace_line.strip()
                        source_path, line_number = trace_line.split(":")
                        source_path = os.path.abspath(source_path)
                        trace_line = source_path + ":" + str(line_number)
                        if (not list_trace) or (list_trace[-1] != trace_line):
                            list_trace.append(trace_line)
                        # if any(loc in line for loc in suspicious_loc_list):
                        #     print(line)
                        #     print(suspicious_loc_list)
                        #     exit(1)
                        #     break
    return list_trace


def collect_suspicious_points(trace_log):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting suspicious points")
    suspect_list = collections.OrderedDict()
    if os.path.exists(trace_log):
        with open(trace_log, 'r') as trace_file:
            for read_line in trace_file:
                if "runtime error:" in read_line:
                    crash_location = read_line.split(": runtime error: ")[0]
                    crash_reason = read_line.split(": runtime error: ")[1]
                    crash_location = ":".join(crash_location.split(":")[:-1])
                    if crash_location not in suspect_list:
                        suspect_list[crash_location] = crash_reason
    return suspect_list


def collect_crash_point(trace_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting crash point")
    crash_location = ""
    if os.path.exists(trace_file_path):
        with open(trace_file_path, 'r') as trace_file:
            for read_line in trace_file:
                if "KLEE: ERROR:" in read_line:
                    read_line = read_line.replace("KLEE: ERROR: ", "")
                    crash_location = read_line.split(": ")[0]
                    break
    return crash_location


def collect_exploit_return_code(output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting exit code")
    return_code = ""
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as output_file:
            for read_line in output_file.readlines():
                if "RETURN CODE:" in read_line:
                    read_line = read_line.replace("RETURN CODE: ", "")
                    return_code = int(read_line)
                    break
    return return_code


def collect_exploit_output(output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting program output")
    output = ""
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as output_file:
            output = output_file.readlines()
    return output


def collect_stack_info(trace_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\tcollecting stack information")
    stack_map = dict()
    if os.path.exists(trace_file_path):
        with open(trace_file_path, 'r') as trace_file:
            is_stack = False
            for read_line in trace_file:
                if is_stack and '#' in read_line:
                    if " at " in read_line:
                        read_line, source_path = str(read_line).split(" at ")
                        source_path, line_number = source_path.split(":")
                        function_name = str(read_line.split(" in ")[1]).split(" (")[0]
                        if source_path not in stack_map.keys():
                            stack_map[source_path] = dict()
                        stack_map[source_path][function_name] = line_number.strip()
                if "Stack:" in read_line:
                    is_stack = True
                    continue
    return stack_map


def collect_last_sym_path(sym_path_file):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    data = ""
    with open(sym_path_file, 'r') as file:
        data = file.read()
    return data
