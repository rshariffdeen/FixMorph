import time
import sys
from app.common import values, definitions, utilities
from app.common.utilities import error_exit, save_current_state, load_state, replace_file, get_source_name_from_slice
from app.tools import fixer
from app.tools import weaver, emitter, reader, filter, writer, logger

file_index = 1
backup_file_list = dict()
modified_source_list = list()

# missing_function_list = dict()
# missing_macro_list = dict()
# missing_header_list = dict()
# missing_data_type_list = dict()
# missing_var_list = dict()


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

    modified_source_list = weaver.weave_functions(values.missing_function_list,
                                                  modified_source_list)


def transplant_missing_global_decl():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global modified_source_list
    modified_source_list = weaver.weave_global_declarations(values.missing_var_list,
                                                            modified_source_list)


def transplant_code():
    global file_index, modified_source_list
    if not values.ast_transformation_info:
        error_exit("nothing to transplant")
    for file_list, generated_data in values.ast_transformation_info.items():
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        slice_file_d = slice_file_c.replace(values.CONF_PATH_C, values.Project_D.path)
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)
        vector_source_d = vector_source_c.replace(values.CONF_PATH_C, values.Project_D.path)

        utilities.shift_slice_source(slice_file_a, slice_file_c)
        segment_code = slice_file_c.replace(vector_source_c + ".", "").split(".")[0]
        segment_identifier_a = slice_file_a.split("." + segment_code + ".")[-1].replace(".slice", "")
        segment_identifier_c = slice_file_c.split("." + segment_code + ".")[-1].replace(".slice", "")

        emitter.sub_sub_title("transforming " + segment_identifier_c + " in " + vector_source_c)
        emitter.highlight("\tOriginal AST script")
        original_script = generated_data[1]
        emitter.emit_ast_script(original_script)

        emitter.highlight("\tGenerated AST script")
        translated_script = generated_data[0]
        emitter.emit_ast_script(translated_script)

        script_file_name = definitions.DIRECTORY_OUTPUT + "/" + str(segment_identifier_c) + "_script"

        with open(script_file_name, 'w') as script_file:
            for transformation_rule in translated_script:
                script_file.write(transformation_rule)

        var_map = values.map_namespace_global[(slice_file_a, slice_file_c)]
        filtered_var_map = filter.filter_namespace_map(var_map, translated_script, vector_source_b)
        writer.write_var_map(filtered_var_map, definitions.FILE_NAMESPACE_MAP_LOCAL)

        weaver.weave_code(vector_source_a,
                          vector_source_b,
                          vector_source_c,
                          script_file_name,
                          modified_source_list
                          )

        replace_file(vector_source_d, slice_file_d)
        utilities.restore_slice_source()


def transform_code():
    global file_index, modified_source_list
    if not values.diff_transformation_info:
        error_exit("nothing to transplant")
    for file_list, diff_file in values.diff_transformation_info.items():
        source_file_a = file_list[0]
        source_file_b = file_list[1]
        source_file_c = file_list[2]
        source_file_d = source_file_c.replace(values.CONF_PATH_C, values.Project_D.path)

        emitter.sub_sub_title("transforming " + source_file_c)

        weaver.weave_code(source_file_a,
                          source_file_b,
                          source_file_c,
                          diff_file,
                          modified_source_list
                          )


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
    global modified_source_list
    # Writer.write_script_info(generated_script_list, Definitions.FILE_SCRIPT_INFO)
    values.MODIFIED_SOURCE_LIST = modified_source_list
    save_current_state()


def weave_slices():
    global file_index, missing_function_list, missing_macro_list, \
        modified_source_list, missing_var_list

    slice_info = dict()
    transformed_list = list()
    if values.DEFAULT_OPERATION_MODE in [0, 3]:
        for file_list, generated_data in values.ast_transformation_info.items():
            transformed_list.append(file_list)
    elif values.DEFAULT_OPERATION_MODE in [1, 2]:
        for file_list, generated_data in values.diff_transformation_info.items():
            transformed_list.append(file_list)
    if not transformed_list:
        error_exit("no slice to weave")
    for file_list in transformed_list:
        slice_file_a = file_list[0]
        slice_file_b = file_list[1]
        slice_file_c = file_list[2]
        slice_file_d = slice_file_c.replace(values.CONF_PATH_C, values.Project_D.path)
        vector_source_a = get_source_name_from_slice(slice_file_a)
        vector_source_b = get_source_name_from_slice(slice_file_b)
        vector_source_c = get_source_name_from_slice(slice_file_c)
        vector_source_d = vector_source_c.replace(values.CONF_PATH_C, values.Project_D.path)
        segment_type = slice_file_c.replace(vector_source_c + ".", "").split(".")[0]
        segment_identifier = slice_file_c.split("." + segment_type + ".")[-1].replace(".slice", "")
        if (vector_source_d, vector_source_b) not in slice_info:
            slice_info[(vector_source_d, vector_source_b)] = list()
        slice_info[(vector_source_d, vector_source_b)].append(slice_file_d)

    emitter.sub_sub_title("weaving slices into source file")
    weaver.weave_slice(slice_info)


def start():
    global modified_source_list
    emitter.title("Applying transformation")
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_WEAVE]:
        if values.DEFAULT_OPERATION_MODE in [0, 3]:
            safe_exec(transplant_code, "transforming slices")
            safe_exec(weave_slices, "weaving slices")
            if values.missing_var_list:
                safe_exec(transplant_missing_global_decl, "transplanting global declarations")
            if values.missing_function_list:
                safe_exec(transplant_missing_functions, "transplanting functions")
            if values.missing_data_type_list:
                safe_exec(transplant_missing_data_types, "transplanting data structures")
            if values.missing_macro_list:
                safe_exec(transplant_missing_macros, "transplanting macros")
            if values.missing_header_list:
                safe_exec(transplant_missing_header, "transplanting header files")
            safe_exec(fixer.check, "correcting syntax errors", modified_source_list)
        elif values.DEFAULT_OPERATION_MODE in [1, 2]:
            safe_exec(transform_code, "transforming slices")
        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")
