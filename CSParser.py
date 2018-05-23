import cs
import os
import sys
import json

project = ''
proj_dir = ''

function_info = dict()
output_dir = 'output/'


def initialize_project():

    global project, proj_dir
    project = cs.project.current()
    proj_dir = sys.argv[1]
    return


def get_function_lines():
    for func in project.procedures():
        source_file = func.file_line()[0].name()

        if source_file not in function_info:
            function_info[source_file] = dict()

        function_name = func.name()
        start_line = func.entry_point().file_line()[1]
        end_line = func.exit_point().file_line()[1]
        function_info[source_file][function_name]['start'] = str(start_line)
        function_info[source_file][function_name]['end'] = str(end_line)


def print_function_lines():
    output_path = output_dir + project.name() + "/" + "function-lines"
    with open(output_path, 'w') as outfile:
        json.dump(function_info, outfile)


def run():

    initialize_project()
    get_function_lines()
    print_function_lines()

    return


run()

