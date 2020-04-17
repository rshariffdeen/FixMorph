import time
import sys
from common import Values, Definitions
from common.Utilities import error_exit, save_current_state, load_state, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
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
    if not Values.translated_script_for_files:
        error_exit("nothing to transplant")
    for file_list, generated_data in Values.translated_script_for_files.items():
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)

        backup_file_orig(vector_source_a)
        backup_file_orig(vector_source_b)
        backup_file_orig(vector_source_c)
        replace_file(slice_file_a, vector_source_a)
        replace_file(slice_file_b, vector_source_b)
        replace_file(slice_file_c, vector_source_c)

        segment_type = slice_file_c.replace(vector_source_c + ".", "").split(".")[0]
        segment_identifier = slice_file_c.split("." + segment_type + ".")[-1]

        Emitter.sub_sub_title("transforming " + segment_identifier + " in " + vector_source_c)
        Emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        Emitter.emit_ast_script(original_script)
        Emitter.highlight("\tGenerated AST script")
        translated_script = generated_data[0]
        Emitter.emit_ast_script(translated_script)
        identified_missing_function_list, \
        identified_missing_macro_list, modified_source_list = Weaver.weave_code(vector_source_a,
                                                                                vector_source_b,
                                                                                vector_source_c,
                                                                                translated_script,
                                                                                modified_source_list)
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

        restore_file_orig(vector_source_a)
        restore_file_orig(vector_source_b)
        restore_file_orig(vector_source_c)


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
    global modified_source_list
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    Values.MODIFIED_SOURCE_LIST = modified_source_list
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
        safe_exec(Fixer.check, "correcting syntax errors", modified_source_list)
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")
