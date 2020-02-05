import time
import sys
from common import Values, Definitions
from common.Utilities import error_exit, save_current_state, load_state
from tools import Emitter, Weaver, Reader, Logger, Fixer, Merger

file_index = 1
backup_file_list = dict()

missing_function_list = dict()
missing_macro_list = dict()
missing_header_list = dict()
missing_data_type_list = dict()
modified_source_list = list()


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


def transplant_missing_header():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, missing_header_list
    if missing_header_list:
        modified_source_list = Weaver.weave_headers(missing_header_list, modified_source_list)


def transplant_missing_macros():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, missing_macro_list
    if missing_macro_list:
        modified_source_list = Weaver.weave_definitions(missing_macro_list, modified_source_list)


def transplant_missing_data_types():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, missing_data_type_list
    if missing_data_type_list:
        modified_source_list = Weaver.weave_data_type(missing_data_type_list, modified_source_list)


def transplant_missing_functions():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global missing_header_list, missing_macro_list, modified_source_list

    missing_header_list_func, \
    missing_macro_list_func, modified_source_list = Weaver.weave_functions(missing_function_list,
                                                                               modified_source_list)

    missing_macro_list = Merger.merge_macro_info(missing_macro_list, missing_macro_list_func)
    missing_header_list = Merger.merge_header_info(missing_header_list, missing_header_list_func)


def transplant_code():
    global file_index, missing_function_list, missing_macro_list, modified_source_list
    for file_list, generated_data in Values.translated_script_for_files.items():
        Emitter.sub_sub_title(file_list[2])
        Emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        Emitter.emit_ast_script(original_script)
        Emitter.highlight("\tGenerated AST script")
        translated_script = generated_data[0]
        Emitter.emit_ast_script(translated_script)
        identified_missing_function_list, \
        identified_missing_macro_list, modified_source_list = Weaver.weave_code(file_list[0], file_list[1], file_list[2], translated_script, modified_source_list)
        file_index += 1
        if missing_function_list:
            if identified_missing_function_list:
                missing_function_list = missing_function_list.update(identified_missing_function_list)
        else:
            missing_function_list = identified_missing_function_list

        if missing_macro_list:
            if identified_missing_macro_list:
                missing_macro_list = Merger.merge_macro_info(missing_macro_list, identified_missing_macro_list)
        else:
            missing_macro_list = identified_missing_macro_list


def load_values():
    load_state()
    if not Values.translated_script_for_files:
        script_info = dict()
        script_list = Reader.read_json(Definitions.FILE_TRANSLATED_SCRIPT_INFO)
        for (path_info, trans_script_info) in script_list:
            script_info[(path_info[0], path_info[1], path_info[2])] = trans_script_info
        Values.translated_script_for_files = script_info

    # Definitions.FILE_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/script-info"


def save_values():
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    # Values.generated_script_for_c_files = generated_script_list
    save_current_state()


def weave():
    global missing_header_list, missing_macro_list, modified_source_list, missing_function_list
    global missing_data_type_list
    Emitter.title("Applying transformation")
    load_values()
    if not Values.SKIP_WEAVE:
        safe_exec(transplant_code, "transplanting code")
        if missing_function_list:
            safe_exec(transplant_missing_functions, "transplanting functions")
        if missing_data_type_list:
            safe_exec(transplant_missing_data_types, "transplanting data structures")
        if missing_macro_list:
            safe_exec(transplant_missing_macros, "transplanting macros")
        if missing_header_list:
            safe_exec(transplant_missing_header, "transplanting header files")
        print(modified_source_list)
        safe_exec(Fixer.check, "correcting syntax errors", modified_source_list)
    else:
        Emitter.special("\n\t-skipping this phase-")
