import time
import sys
from common import Definitions, Values
from common.Utilities import error_exit, save_current_state, load_state
from tools import Emitter, Reader, Writer, Logger, Translator


translated_script_list = dict()


def translate_scripts():
    global translated_script_list
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not Values.generated_script_files:
        error_exit("nothing to translate")
    translated_script_list = Translator.translate_script_list(Values.generated_script_files)


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
    if not Values.ast_map:
        map_info = dict()
        map_list = Reader.read_json(Definitions.FILE_MAP_INFO)
        for (file_path_info, node_map) in map_list:
            map_info[(file_path_info[0], file_path_info[1], file_path_info[2])] = node_map
        Values.ast_map = map_info

    Definitions.FILE_TRANSLATED_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/trans-script-info"


def save_values():
    Writer.write_script_info(translated_script_list, Definitions.FILE_TRANSLATED_SCRIPT_INFO)
    Values.translated_script_for_files = translated_script_list
    save_current_state()


def translate():
    global translated_script_list
    Emitter.title("Translate AST Script")
    load_values()
    if not Values.SKIP_TRANSLATION:
        safe_exec(translate_scripts, "translation of generated scripts")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")

