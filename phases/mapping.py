import sys
import time
from common import definitions, values
from common.utilities import execute_command, error_exit, save_current_state
from tools import emitter, reader, writer, logger, mapper


def generate_map():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    values.ast_map = mapper.generate_ast_map(values.generated_script_files)


def load_values():
    if not values.generated_script_files:
        script_info = dict()
        script_list = reader.read_json(definitions.FILE_SCRIPT_INFO)
        for (vec_path_info, vec_info) in script_list:
            script_info[(vec_path_info[0], vec_path_info[1], vec_path_info[2])] = vec_info
        values.generated_script_files = script_info

    definitions.FILE_MAP_INFO = definitions.DIRECTORY_OUTPUT + "/map-info"
    definitions.FILE_NAMESPACE_MAP = definitions.DIRECTORY_OUTPUT + "/namespace-map"
    definitions.FILE_NAMESPACE_MAP_LOCAL = definitions.DIRECTORY_OUTPUT + "/namespace-map-local"
    definitions.FILE_NAMESPACE_MAP_GLOBAL = definitions.DIRECTORY_OUTPUT + "/namespace-map-global"


def safe_exec(function_def, title, *args):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def save_values():
    writer.write_map_info(values.ast_map, definitions.FILE_MAP_INFO)
    save_current_state()


def map():
    emitter.title("Variable Mapping")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_MAPPING]:
        if not values.generated_script_files:
            error_exit("no ast to map")
        safe_exec(generate_map, 'derivation of variable/data-structure map')
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")
