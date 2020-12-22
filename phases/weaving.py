import time
import sys
from common import values, definitions
from common.utilities import error_exit, save_current_state, load_state, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import emitter, weaver, reader, logger, fixer, merger

file_index = 1
backup_file_list = dict()

missing_function_list = dict()
missing_macro_list = dict()
missing_header_list = dict()
missing_data_type_list = dict()
modified_source_list = list()


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


def transplant_missing_header():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list
    if values.missing_header_list:
        modified_source_list = weaver.weave_headers(values.missing_header_list, modified_source_list)


def transplant_missing_macros():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, missing_macro_list
    if values.missing_macro_list:
        modified_source_list = weaver.weave_definitions(values.missing_macro_list, modified_source_list)


def transplant_missing_data_types():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list
    if values.missing_data_type_list:
        modified_source_list = weaver.weave_data_type(values.missing_data_type_list, modified_source_list)


def transplant_missing_functions():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list

    modified_source_list = weaver.weave_functions(missing_function_list,
                                                  modified_source_list)


def transplant_code():
    global file_index, modified_source_list
    if not values.translated_script_for_files:
        error_exit("nothing to transplant")
    for file_list, generated_data in values.translated_script_for_files.items():
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        slice_file_d = slice_file_c.replace(values.PATH_C, values.Project_D.path)
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)
        vector_source_d = vector_source_c.replace(values.PATH_C, values.Project_D.path)

        backup_file_orig(vector_source_a)
        backup_file_orig(vector_source_b)
        backup_file_orig(vector_source_c)
        backup_file_orig(vector_source_d)
        replace_file(slice_file_a, vector_source_a)
        replace_file(slice_file_b, vector_source_b)
        replace_file(slice_file_c, vector_source_c)
        replace_file(slice_file_d, vector_source_d)

        segment_code = slice_file_c.replace(vector_source_c + ".", "").split(".")[0]
        segment_identifier_a = slice_file_a.split("." + segment_code + ".")[-1].replace(".slice", "")
        segment_identifier_c = slice_file_c.split("." + segment_code + ".")[-1].replace(".slice", "")

        emitter.sub_sub_title("transforming " + segment_identifier_c + " in " + vector_source_c)
        emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        emitter.emit_ast_script(original_script)
        script_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(segment_identifier_c) + "_script"
        translated_script = list()
        with open(script_file_name, "r") as script_file:
            translated_script = script_file.readlines()
        emitter.highlight("\tGenerated AST script")
        emitter.emit_ast_script(translated_script)

        weaver.weave_code(vector_source_a,
                          vector_source_b,
                          vector_source_c,
                          script_file_name,
                          modified_source_list
                          )

        restore_file_orig(vector_source_a)
        restore_file_orig(vector_source_b)
        restore_file_orig(vector_source_c)
        replace_file(vector_source_d, slice_file_d)
        restore_file_orig(vector_source_d)


def load_values():
    load_state()
    if not values.translated_script_for_files:
        script_info = dict()
        script_list = reader.read_json(definitions.FILE_TRANSLATED_SCRIPT_INFO)
        for (path_info, trans_script_info) in script_list:
            script_info[(path_info[0], path_info[1], path_info[2])] = trans_script_info
        values.translated_script_for_files = script_info

    definitions.FILE_SCRIPT_INFO = definitions.DIRECTORY_OUTPUT + "/script-info"
    definitions.FILE_TEMP_FIX = definitions.DIRECTORY_TMP + "/temp-fix"


def save_values():
    global modified_source_list
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    values.MODIFIED_SOURCE_LIST = modified_source_list
    save_current_state()


def weave_slices():
    global file_index, missing_function_list, missing_macro_list, modified_source_list
    if not values.translated_script_for_files:
        error_exit("no slice to weave")
    slice_info = dict()
    for file_list, generated_data in values.translated_script_for_files.items():
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        slice_file_d = slice_file_c.replace(values.PATH_C, values.Project_D.path)
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)
        vector_source_d = vector_source_c.replace(values.PATH_C, values.Project_D.path)
        segment_type = slice_file_c.replace(vector_source_c + ".", "").split(".")[0]
        segment_identifier = slice_file_c.split("." + segment_type + ".")[-1].replace(".slice", "")
        if (vector_source_d, vector_source_b) not in slice_info:
            slice_info[(vector_source_d, vector_source_b)] = list()
        slice_info[(vector_source_d, vector_source_b)].append(slice_file_d)

    emitter.sub_sub_title("weaving slices into source file")
    weaver.weave_slice(slice_info)


def weave():
    global modified_source_list
    emitter.title("Applying transformation")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_WEAVE]:
        safe_exec(transplant_code, "transforming slices")
        safe_exec(weave_slices, "weaving slices")
        if values.missing_function_list:
            safe_exec(transplant_missing_functions, "transplanting functions")
        if values.missing_data_type_list:
            safe_exec(transplant_missing_data_types, "transplanting data structures")
        if values.missing_macro_list:
            safe_exec(transplant_missing_macros, "transplanting macros")
        if values.missing_header_list:
            safe_exec(transplant_missing_header, "transplanting header files")
        safe_exec(fixer.check, "correcting syntax errors", modified_source_list)
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")
