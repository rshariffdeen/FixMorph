
import Common
from Utils import exec_com, err_exit
import Print


def generate_map(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Print.blue("Generating mapping: " + name_a + Common.TO + name_b + "...")
    try:
        extra_arg = ""
        if file_a[-2:] == ".h":
            extra_arg = " --"
        command = Common.DIFF_COMMAND + " -s=" + Common.DIFF_SIZE + " -dump-matches " + \
            file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += "| grep '^Match ' "
        command += " > " + output_file
        exec_com(command, False)
    except Exception as e:
        err_exit(e, "Unexpected fail at generating map: " + output_file)


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


def get_mapping(map_file_name):
    node_map = dict()
    with open(map_file_name, 'r', errors='replace') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == Common.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Common.TO)
                    node_map[node_a] = node_c
                except Exception as exception:
                    err_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


def generate():
    Print.title("Variable Mapping")
    Print.sub_title("Variable mapping for header files")
    if len(Common.generated_script_for_header_files) == 0:
        Print.blue("\t -nothing-to-do")
    else:
        for file_list, generated_data in Common.generated_script_for_header_files.items():
            map_file_name = "output/diff_script_AC"
            generate_map(file_list[0], file_list[2], map_file_name)
            variable_map = get_mapping(map_file_name)
            Common.variable_map[file_list] = variable_map

    Print.sub_title("Variable mapping for C files")
    if len(Common.generated_script_for_c_files) == 0:
        Print.blue("\t -nothing-to-do")
    else:
        for file_list, generated_data in Common.generated_script_for_c_files.items():
            map_file_name = "output/diff_script_AC"
            generate_map(file_list[0], file_list[2], map_file_name)
            variable_map = get_mapping(map_file_name)
            Common.variable_map[file_list] = variable_map
