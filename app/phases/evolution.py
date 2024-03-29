import time
import sys
from app.common import values, definitions, utilities
from app.common.utilities import error_exit, save_current_state, load_state, get_source_name_from_slice
from app.tools import evolver, merger
from app.tools import emitter, reader, logger
from app.ast import ast_generator

file_index = 1
backup_file_list = dict()


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


def evolve_macros():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if values.missing_macro_list:
        header_list, macro_list = evolver.evolve_definitions(values.missing_macro_list)
        values.missing_macro_list = macro_list
        values.missing_header_list = merger.merge_header_info(values.missing_header_list, header_list)


def evolve_data_types():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if values.missing_data_type_list:
        missing_header_list, missing_macro_list = evolver.evolve_data_type(values.missing_data_type_list)


def evolve_functions():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if values.missing_function_list:
        header_list, macro_list, function_list = evolver.evolve_functions(values.missing_function_list, 
                                                                          values.DEFAULT_TRANSPLANT_DEPTH)
        values.missing_macro_list = merger.merge_macro_info(values.missing_macro_list, macro_list)
        values.missing_header_list = merger.merge_header_info(values.missing_header_list, header_list)
        values.missing_function_list = function_list


def evolve_code():
    global file_index
    if not values.ast_transformation_info:
        error_exit("nothing to evolve")
    updated_info = dict()
    for list_tuple in values.ast_transformation_info.items():
        file_list, generated_data = list_tuple
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        slice_file_d = slice_file_c.replace(values.CONF_PATH_C, values.Project_D.path)
        slice_file_list = (slice_file_a, slice_file_b, slice_file_c, slice_file_d)
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)
        vector_source_d = vector_source_c.replace(values.CONF_PATH_C, values.Project_D.path)
        source_file_list = (vector_source_a, vector_source_b, vector_source_c, vector_source_d)

        ast_tree_global_a = ast_generator.get_ast_json(vector_source_a, values.DONOR_REQUIRE_MACRO, True)
        ast_tree_global_b = ast_generator.get_ast_json(vector_source_b, values.DONOR_REQUIRE_MACRO, True)
        ast_tree_global_c = ast_generator.get_ast_json(vector_source_c, values.DONOR_REQUIRE_MACRO, True)

        utilities.shift_slice_source(slice_file_a, slice_file_c)

        segment_code = slice_file_c.replace(vector_source_c + ".", "").split(".")[0]
        segment_identifier_a = slice_file_a.split("." + segment_code + ".")[-1].replace(".slice", "")
        segment_identifier_c = slice_file_c.split("." + segment_code + ".")[-1].replace(".slice", "")

        emitter.sub_sub_title("evolving " + segment_identifier_c + " in " + vector_source_c)
        # emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        # emitter.emit_ast_script(original_script)
        # emitter.highlight("\tGenerated AST script")
        translated_script = generated_data[0]
        # emitter.emit_ast_script(translated_script)

        identified_function_list, \
        identified_macro_list, evolved_script, \
        identified_var_list, identified_data_type_list = evolver.evolve_code(slice_file_list,
                                                                             source_file_list,
                                                                             translated_script,
                                                                             segment_identifier_a,
                                                                             segment_identifier_c,
                                                                             segment_code,
                                                                             ast_tree_global_a,
                                                                             ast_tree_global_b,
                                                                             ast_tree_global_c
                                                                             )
        updated_data = (evolved_script, original_script)
        updated_info[file_list] = updated_data
        emitter.highlight("\tEvolved AST script")
        emitter.emit_ast_script(evolved_script)
        file_index += 1
        if values.missing_function_list:
            if identified_function_list:
                values.missing_function_list.update(identified_function_list)
        else:
            values.missing_function_list = identified_function_list

        if values.missing_var_list:
            if identified_var_list:
                values.missing_var_list.update(identified_var_list)
        else:
            values.missing_var_list = identified_var_list

        if values.missing_data_type_list:
            if identified_data_type_list:
                values.missing_data_type_list.update(identified_data_type_list)
        else:
            values.missing_data_type_list = identified_data_type_list

        if values.missing_macro_list:
            if identified_macro_list:
                values.missing_macro_list = merger.merge_macro_info(values.missing_macro_list, identified_macro_list)
        else:
            values.missing_macro_list = identified_macro_list

        utilities.replace_file(vector_source_d, slice_file_d)
        utilities.restore_slice_source()

    values.ast_transformation_info = updated_info


def load_values():
    load_state()
    if not values.ast_transformation_info:
        script_info = dict()
        script_list = reader.read_json(definitions.FILE_TRANSLATED_SCRIPT_INFO)
        for (path_info, trans_script_info) in script_list:
            script_info[(path_info[0], path_info[1], path_info[2])] = trans_script_info
        values.ast_transformation_info = script_info

    definitions.FILE_SCRIPT_INFO = definitions.DIRECTORY_OUTPUT + "/script-info"
    definitions.FILE_TEMP_FIX = definitions.DIRECTORY_TMP + "/temp-fix"


def save_values():
    save_current_state()


def start():
    emitter.title("Evolve transformation")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_EVOLUTION]:
        safe_exec(evolve_code, "evaluate code slices")
        if values.missing_function_list:
            safe_exec(evolve_functions, "evolve function definitions")
        if values.missing_data_type_list:
            safe_exec(evolve_data_types, "evolve data structures")
        if values.missing_macro_list:
            safe_exec(evolve_macros, "evolve macros")
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")
