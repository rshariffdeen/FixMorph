import cs
import os
import json


project = ''


function_info = dict()
output_dir = 'crochet-output/'


def initialize_project():
    global project
    project = cs.project.current()
    return


def create_output_directories():
    if not os.path.isdir(output_dir):
        os.system("mkdir " + output_dir)


def get_function_details():
    for func in project.procedures():
        function_name = func.name()
        #print function_name
        if '#' in function_name:
            continue
        try:
            source_file = func.file_line()
            source_file_path = source_file[0].name()
            if source_file_path not in function_info:
                function_info[source_file_path] = dict()

            if "/opt" in str(source_file_path):
                continue

            function_info[source_file_path][function_name] = dict()
            function_info[source_file_path][function_name]['variable-list'] = get_variable_list(func)
            function_info[source_file_path][function_name]['line-range'] = get_function_lines(func)

        except Exception as e:
            print "exception processing function ", function_name
            print(e)
            continue


def get_function_lines(procedure):
    start_line = procedure.entry_point().file_line()[1]
    end_line = procedure.exit_point().file_line()[1]
    line_range = dict()
    line_range['start'] = str(start_line)
    line_range['end'] = str(end_line)
    return line_range


def print_function_info():
    output_path = output_dir + "/" + "function-info"
    with open(output_path, 'w') as outfile:
        json.dump(function_info, outfile)


def get_variable_line_number_list(line_list, source_file_name):
    line_number_list = list()
    for line in line_list:
        try:
            file_name = line.file_line()[0].name()
            if file_name == source_file_name:
                line_number = line.file_line()[1]
                if line_number not in line_number_list:
                    line_number_list.append(line_number)

        except Exception as e:
            # print "cannot determine line for variable "
            continue
    return line_number_list


def get_variable_list(procedure):
    symbol_list = list(procedure.local_symbols())
    var_list = dict()
    source_file_name = procedure.file_line()[0].name()

    for var in symbol_list:
        #print var
        var_info = dict()
        var_name = var.name().split("-")[0]

        var_info['type'] = var.get_type().get_class().name()
        declaration_lines = get_variable_line_number_list(var.declarations(), source_file_name)
        var_info['dec-line-numbers'] = declaration_lines

        used_lines = get_variable_line_number_list(list(var.used_points()), source_file_name)
        var_info['use-line-numbers'] = used_lines

        killed_lines = get_variable_line_number_list(list(var.killed_points()) + list(var.may_killed_points()),
                                                     source_file_name)
        var_info['killed-line-numbers'] = killed_lines
        var_list[var_name] = var_info

    return var_list


def run():
    initialize_project()
    create_output_directories()
    get_function_details()
    print_function_info()
    exit(0)


run()
