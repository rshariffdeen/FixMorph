import time
import sys
from common import values, definitions
from common.utilities import error_exit, save_current_state, load_state, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import Emitter, Evolver, Reader, Logger, Merger


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def evaluate_code():
    global file_index
    if not values.translated_script_for_files:
        error_exit("nothing to evolve")
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

        Emitter.sub_sub_title("evolving " + segment_identifier_c + " in " + vector_source_c)
        Emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        Emitter.emit_ast_script(original_script)
        Emitter.highlight("\tGenerated AST script")
        translated_script = generated_data[0]
        Emitter.emit_ast_script(translated_script)

        identified_function_list, \
        identified_macro_list = Evolver.evolve_code(
                                                    vector_source_a,
                                                    vector_source_b,
                                                    vector_source_c,
                                                    translated_script,
                                                    segment_identifier_a,
                                                    segment_identifier_c,
                                                    segment_code
                                                    )
        file_index += 1
        if values.missing_function_list:
            if identified_function_list:
                values.missing_function_list = values.missing_function_list.update(identified_function_list)
        else:
            values.missing_function_list = identified_function_list

        if values.missing_macro_list:
            if identified_macro_list:
                values.missing_macro_list = Merger.merge_macro_info(values.missing_macro_list, identified_macro_list)
        else:
            values.missing_macro_list = identified_macro_list

        restore_file_orig(vector_source_a)
        restore_file_orig(vector_source_b)
        restore_file_orig(vector_source_c)
        replace_file(vector_source_d, slice_file_d)
        restore_file_orig(vector_source_d)


def load_values():
    load_state()
    if not values.translated_script_for_files:
        script_info = dict()
        script_list = Reader.read_json(definitions.FILE_TRANSLATED_SCRIPT_INFO)
        for (path_info, trans_script_info) in script_list:
            script_info[(path_info[0], path_info[1], path_info[2])] = trans_script_info
        values.translated_script_for_files = script_info

    definitions.FILE_SCRIPT_INFO = definitions.DIRECTORY_OUTPUT + "/script-info"
    definitions.FILE_TEMP_FIX = definitions.DIRECTORY_TMP + "/temp-fix"


def save_values():
    save_current_state()


def evaluate():
    Emitter.title("Evaluating transformation")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_EVALUATE]:
        safe_exec(evaluate_code, "evaluate code slices")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")
