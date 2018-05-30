import cs
import os, signal
import sys
import json
import operator

project = ''
slice_function_name = ''
slice_function_file_name = ''
function_info = dict()
output_dir = 'crochet-output/'


def initialize_project():
    global project, slice_function_name, slice_function_file_name
    project = cs.project.current()
    slice_function_name = sys.argv[1]
    slice_function_file_name = sys.argv[2]
    return


def generate_variable_slice():
    for func in project.procedures():
        if func.name() == slice_function_name:
            source_file_name = func.file_line()[0].name()
            if source_file_name == slice_function_file_name:
                point_list = func.points()
                var_list = list(func.local_symbols())
                for var in var_list:
                    var_name = var.name()
                    if "$return" in var_name or "$result" in var_name:
                        continue
                    var_name = var_name.split("-")[0]
                    slice_lines = get_variable_slice(point_list, var)
                    output_slice_file(slice_function_file_name.split("/")[-1], slice_function_name, var_name, slice_lines)


def output_slice_file(file_name, function_name, variable_name, line_list):
    output_path = output_dir + "/" + file_name.replace(".c", '') + "-" + function_name + "-" + variable_name + ".vec"
    with open(output_path, 'w') as slice_file:
        for line in line_list:
            slice_file.write("%s\n" % str(line))


def get_variable_slice(point_list, variable):

    if '$return' in variable.name():
        return list()

    filter_point_types = ["global-actual-in", "global-actual-out",
                          "global-formal-in", "global-formal-out",
                          "in", "out", "auxiliary"]

    declarations = variable.declarations()

    sliced_lines = dict()
    chopped_points = declarations.chop(point_list)
    chopped_points = chopped_points.intersect(point_list)

    if chopped_points:
        for point in chopped_points:
            if hasattr(point, 'get_kind'):
                if str(point.get_kind()) not in filter_point_types:
                    statement = point.__str__()
                    if '$result' not in statement and '$return' not in statement:
                        line_number = point.compunit_line()[1]
                        sliced_lines[line_number] = statement

    sorted_sliced_lines = sorted(sliced_lines.items(), key=operator.itemgetter(0))

    return list(sorted_sliced_lines)


def get_variable_list(procedure):
    symbol_list = list(procedure.local_symbols())
    var_list = dict()
    source_file_name = procedure.file_line()[0].name()

    for var in symbol_list:
        var_info = dict()
        var_name = var.name().split("-")[0]

        var_info['type'] = var.get_type().get_class().name()
        declaration_lines = get_variable_line_number_list(var.declarations(), source_file_name)
        var_info['dec-line-numbers'] = declaration_lines

        used_lines = get_variable_line_number_list(list(var.used_points()), source_file_name)
        var_info['use-line-numbers'] = used_lines

        successive_lines = get_variable_line_number_list(list(var.used_points()), source_file_name)
        killed_lines = get_variable_line_number_list(list(var.killed_points()) + list(var.may_killed_points()),
                                                     source_file_name)
        var_info['killed-line-numbers'] = killed_lines

        # slice_lines = get_variable_slice(procedure.points(), var)
        # var_info['sliced-lines'] = slice_lines

        var_list[var_name] = var_info
    return var_list


def run():
    initialize_project()
    generate_variable_slice()
    exit(0)


run()
