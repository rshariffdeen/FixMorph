import time
import sys
from app.common import definitions, values
from app.common.utilities import error_exit, save_current_state, load_state
from app.tools import translator, emitter, reader, writer, logger

translated_script_list = dict()


def translate_scripts():
    global translated_script_list
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not values.diff_transformation_info:
        error_exit("nothing to translate")

    generated_script_list = values.diff_transformation_info
    translated_script_list = dict()
    for file_list, generated_data in generated_script_list.items():
        emitter.sub_sub_title(file_list[0])
        translated_script, original_script = translator.translate_script_list(file_list, generated_data)
        translated_script_list[file_list] = (translated_script, original_script)
        emitter.highlight("\tTranslated AST script")
        emitter.emit_ast_script(translated_script)


def safe_exec(function_def, title, *args):
    start_time = time.time()
    emitter.sub_title("Starting " + title + "...")
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
    if values.DEFAULT_OPERATION_MODE not in [1, 2]:
        if not values.ast_map:
            values.ast_map = reader.read_ast_map(definitions.FILE_AST_MAP_LOCAL)
        if not values.map_namespace_global:
            values.map_namespace_global = reader.read_namespace_map(definitions.FILE_NAMESPACE_MAP_GLOBAL)

    definitions.FILE_TRANSLATED_SCRIPT_INFO = definitions.DIRECTORY_OUTPUT + "/trans-script-info"


def save_values():
    writer.write_script_info(translated_script_list, definitions.FILE_TRANSLATED_SCRIPT_INFO)
    values.ast_transformation_info = translated_script_list
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

