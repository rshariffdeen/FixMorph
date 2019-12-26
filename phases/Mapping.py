from common import Definitions, Values
from common.Utilities import execute_command, error_exit, save_current_state
from tools import Emitter, Reader, Writer


def generate_map(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Emitter.normal("Generating mapping: " + name_a + Definitions.TO + name_b + "...")
    try:
        extra_arg = ""
        if file_a[-2:] == ".h":
            extra_arg = " --"
        command = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -dump-matches " + \
                  file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += "| grep '^Match ' "
        command += " > " + output_file
        execute_command(command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating map: " + output_file)


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
    with open(map_file_name, 'r') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == Definitions.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Definitions.TO)
                    node_map[node_a] = node_c
                except Exception as exception:
                    error_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


def load_values():
    if not Values.generated_script_for_c_files:
        script_info = dict()
        script_list = Reader.read_json(Definitions.FILE_SCRIPT_INFO)
        for (vec_path_info, vec_info) in script_list:
            script_info[vec_path_info] = vec_info
        Values.generated_script_for_c_files = script_info

    # Definitions.FILE_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/script-info"


def save_values():
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    # Values.generated_script_for_c_files = generated_script_list
    save_current_state()


def map():
    Emitter.title("Variable Mapping")

    load_values()
    if not Values.SKIP_MAPPING:
        # Emitter.sub_title("Variable mapping for header files")
        # if len(Values.generated_script_for_header_files) == 0:
        #     Emitter.normal("\t -nothing-to-do")
        # else:
        #     for file_list, generated_data in Values.generated_script_for_header_files.items():
        #         map_file_name = "output/diff_script_AC"
        #         generate_map(file_list[0], file_list[2], map_file_name)
        #         variable_map = get_mapping(map_file_name)
        #         Values.variable_map[file_list] = variable_map
        #
        Emitter.sub_title("Variable mapping for C files")
        if len(Values.generated_script_for_c_files) == 0:
            Emitter.normal("\t -nothing-to-do")
        else:
            for file_list, generated_data in Values.generated_script_for_c_files.items():
                map_file_name = "output/diff_script_AC"
                generate_map(file_list[0], file_list[2], map_file_name)
                variable_map = get_mapping(map_file_name)
                Values.variable_map[file_list] = variable_map
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")