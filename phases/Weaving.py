import time
from common import Values, Definitions
from common.Utilities import error_exit, save_current_state, load_state
from tools import Emitter, Weaver, Reader, Writer

file_index = 1
backup_file_list = dict()


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Emitter.error("Crash during " + description + ", after " + duration + " seconds.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def load_values():
    load_state()
    if not Values.translated_script_for_files:
        # map_info = dict()
        # map_list = Reader.read_json(Definitions.FILE_MAP_INFO)
        # for (file_path_info, node_map) in map_list:
        #     map_info[(file_path_info[0], file_path_info[1])] = node_map
        Values.translated_script_for_files = Reader.read_json(Definitions.FILE_TRANSLATED_SCRIPT_INFO)

    # Definitions.FILE_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/script-info"


def save_values():
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    # Values.generated_script_for_c_files = generated_script_list
    save_current_state()


def weave():
    global file_index
    Emitter.title("Applying transformation")
    for file_list, generated_data in Values.translated_script_for_files.items():
        Emitter.sub_title("Transforming file " + file_list[2])
        Emitter.special("Original AST script")
        original_script = generated_data[1]
        Emitter.emit_ast_script(original_script)
        Emitter.special("Generated AST script")
        translated_script = generated_data[0]
        Emitter.emit_ast_script(translated_script)
        Weaver.apply_patch(file_list[0], file_list[1], file_list[2], translated_script)
        file_index += 1
