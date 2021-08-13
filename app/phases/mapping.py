import sys
import time
from app.common import definitions, values
from app.common.utilities import error_exit, save_current_state
from app.tools import mapper, emitter, reader, writer, logger


def generate_map():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    generated_script_files = values.diff_transformation_info
    ast_map_global = dict()
    namespace_map_global = dict()
    if len(generated_script_files) == 0:
        emitter.normal("\t -nothing-to-do")
    else:
        for file_list, generated_data in generated_script_files.items():
            slice_file_a = file_list[0]
            slice_file_c = file_list[2]
            emitter.sub_sub_title(slice_file_a)
            ast_node_map, namespace_map = mapper.generate_map(file_list)
            # writer.write_ast_map(ast_node_map, definitions.DIRECTORY_OUTPUT + "/ast-map-local")
            ast_map_global[(slice_file_a, slice_file_c)] = ast_node_map
            namespace_map_global[(slice_file_a, slice_file_c)] = namespace_map
    values.ast_map = ast_map_global
    values.map_namespace_global = namespace_map_global


def load_values():
    if not values.diff_transformation_info:
        script_info = dict()
        script_list = reader.read_json(definitions.FILE_SCRIPT_INFO)
        for (vec_path_info, vec_info) in script_list:
            script_info[(vec_path_info[0], vec_path_info[1], vec_path_info[2])] = vec_info
        values.diff_transformation_info = script_info

    definitions.FILE_AST_MAP_LOCAL = definitions.DIRECTORY_OUTPUT + "/map-info"
    # definitions.FILE_NAMESPACE_MAP = definitions.DIRECTORY_OUTPUT + "/namespace-map"
    definitions.FILE_DATATYPE_MAP = definitions.DIRECTORY_OUTPUT + "/datatype-map"
    definitions.FILE_NAMESPACE_MAP_LOCAL = definitions.DIRECTORY_OUTPUT + "/namespace-map-local"
    definitions.FILE_NAMESPACE_MAP_GLOBAL = definitions.DIRECTORY_OUTPUT + "/namespace-map-global"


def safe_exec(function_def, title, *args):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    emitter.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        logger.information("running " + str(function_def))
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


def save_values():
    writer.write_ast_map(values.ast_map, definitions.FILE_AST_MAP_LOCAL)
    writer.write_namespace_map(values.map_namespace_global, definitions.FILE_NAMESPACE_MAP_GLOBAL)
    save_current_state()


def start():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    load_values()
    if values.PHASE_SETTING[definitions.PHASE_MAPPING]:
        emitter.title("Variable Mapping")
        if not values.diff_transformation_info:
            error_exit("no ast to map")
        safe_exec(generate_map, 'derivation of variable/data-structure map')
        save_values()

