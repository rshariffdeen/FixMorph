import time
import sys
from common import definitions, values
from common.utilities import error_exit, save_current_state, load_state
from tools import emitter, reader, writer, logger, translator


translated_script_list = dict()


def translate_scripts():
    global translated_script_list
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not values.generated_script_files:
        error_exit("nothing to translate")

    generated_script_list = values.generated_script_files
    translated_script_list = dict()
    for file_list, generated_data in generated_script_list.items():
        emitter.sub_title(file_list[0])
        translated_script, original_script = translator.translate_script_list(file_list, generated_data)
        translated_script_list[file_list] = (translated_script, original_script)


def safe_exec(function_def, title, *args):
    start_time = time.time()
    emitter.normal("\tStarting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
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


def load_values():
    load_state()
    if not values.ast_map:
        values.ast_map = reader.read_ast_map(definitions.FILE_AST_MAP_LOCAL)
    if not values.map_namespace_global:
        values.map_namespace_global = reader.read_namespace_map(definitions.FILE_NAMESPACE_MAP_GLOBAL)

    definitions.FILE_TRANSLATED_SCRIPT_INFO = definitions.DIRECTORY_OUTPUT + "/trans-script-info"


def save_values():
    writer.write_script_info(translated_script_list, definitions.FILE_TRANSLATED_SCRIPT_INFO)
    values.translated_script_for_files = translated_script_list
    save_current_state()


def start():
    global translated_script_list
    emitter.title("Translate AST Script")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_TRANSLATION]:
        safe_exec(translate_scripts, "translation of generated scripts")
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")

