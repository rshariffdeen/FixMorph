import sys
import time
from common import Definitions, Values
from common.Utilities import execute_command, error_exit, save_current_state
from tools import Emitter, Reader, Writer, Logger, Mapper


def generate_map():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Values.ast_map = Mapper.generate(Values.generated_script_files)


def load_values():
    if not Values.generated_script_files:
        script_info = dict()
        script_list = Reader.read_json(Definitions.FILE_SCRIPT_INFO)
        for (vec_path_info, vec_info) in script_list:
            script_info[(vec_path_info[0], vec_path_info[1], vec_path_info[2])] = vec_info
        Values.generated_script_files = script_info

    Definitions.FILE_MAP_INFO = Definitions.DIRECTORY_OUTPUT + "/map-info"


def safe_exec(function_def, title, *args):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    Emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        Logger.information("running " + str(function_def))
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


def save_values():
    Writer.write_map_info(Values.ast_map, Definitions.FILE_MAP_INFO)
    save_current_state()


def map():
    Emitter.title("Variable Mapping")
    load_values()

    if not Values.SKIP_MAPPING:
        if not Values.generated_script_files:
            error_exit("no ast to map")
        safe_exec(generate_map, 'deriving variable/data-structure mapping')
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")
