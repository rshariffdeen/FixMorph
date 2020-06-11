import time
import sys
from common import Values, Definitions
from common.Utilities import error_exit, save_current_state, load_state, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import Emitter, Evolver, Reader, Logger, Merger

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


def evolve_headers():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, header_list
    if header_list:
        modified_source_list = Weaver.weave_headers(header_list, modified_source_list)


def evolve_macros():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, macro_list
    if macro_list:
        modified_source_list = Weaver.weave_definitions(macro_list, modified_source_list)


def evolve_data_types():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list, data_type_list
    if data_type_list:
        modified_source_list = Weaver.weave_data_type(data_type_list, modified_source_list)


def evolve_functions():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global header_list, macro_list, modified_source_list

    header_list_func, \
    macro_list_func, modified_source_list = Weaver.weave_functions(function_list,
                                                                               modified_source_list)

    macro_list = Merger.merge_macro_info(macro_list, macro_list_func)
    header_list = Merger.merge_header_info(header_list, header_list_func)


def evolve_code():
    global file_index
    if not Values.translated_script_for_files:
        error_exit("nothing to evolve")
    for file_list, generated_data in Values.translated_script_for_files.items():
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        slice_file_d = slice_file_c.replace(Values.PATH_C, Values.Project_D.path)
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)
        vector_source_d = vector_source_c.replace(Values.PATH_C, Values.Project_D.path)

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

        Emitter.sub_sub_title("evolving " + segment_identifier_c + " in " + vector_source_c)
        Emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        Emitter.emit_ast_script(original_script)
        Emitter.highlight("\tGenerated AST script")
        translated_script = generated_data[0]
        Emitter.emit_ast_script(translated_script)

        identified_function_list, \
        identified_macro_list = Evolver.evolve_code(vector_source_a,
                                                    vector_source_b,
                                                    vector_source_c,
                                                    translated_script,
                                                    segment_identifier_a,
                                                    segment_identifier_c,
                                                    segment_code
                                                    )
        file_index += 1
        if Values.missing_function_list:
            if identified_function_list:
                Values.missing_function_list = Values.missing_function_list.update(identified_function_list)
        else:
            Values.missing_function_list = identified_function_list

        if Values.missing_macro_list:
            if identified_macro_list:
                Values.missing_macro_list = Merger.merge_macro_info(Values.missing_macro_list, identified_macro_list)
        else:
            Values.missing_macro_list = identified_macro_list

        restore_file_orig(vector_source_a)
        restore_file_orig(vector_source_b)
        restore_file_orig(vector_source_c)
        replace_file(vector_source_d, slice_file_d)
        restore_file_orig(vector_source_d)


def load_values():
    load_state()
    if not Values.translated_script_for_files:
        script_info = dict()
        script_list = Reader.read_json(Definitions.FILE_TRANSLATED_SCRIPT_INFO)
        for (path_info, trans_script_info) in script_list:
            script_info[(path_info[0], path_info[1], path_info[2])] = trans_script_info
        Values.translated_script_for_files = script_info

    Definitions.FILE_SCRIPT_INFO = Definitions.DIRECTORY_OUTPUT + "/script-info"
    Definitions.FILE_TEMP_FIX = Definitions.DIRECTORY_TMP + "/temp-fix"


def save_values():
    global modified_source_list
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    Values.MODIFIED_SOURCE_LIST = modified_source_list
    save_current_state()


def evolve():
    Emitter.title("evolve transformation")
    load_values()
    if not Values.SKIP_EVOLVE:
        safe_exec(evolve_code, "evolve code slices")
        if Values.missing_function_list:
            safe_exec(evolve_functions, "evolve function definitions")
        if Values.missing_data_type_list:
            safe_exec(evolve_data_types, "evolve data structures")
        if Values.missing_macro_list:
            safe_exec(evolve_macros, "evolve macros")
        if Values.missing_header_list:
            safe_exec(evolve_headers, "evolve header files")      
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")
