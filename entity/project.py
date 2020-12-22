# -*- coding: utf-8 -*-

import os
from common.utilities import error_exit, clean_files, execute_command
from tools import emitter


class Project:
    
    def __init__(self, path, name):
        emitter.information("creating project for " + path)
        if not (os.path.isdir(path)):
            error_exit(name + " is not an appropriate directory path.", path)
        if path[-1] != "/":
            path += "/"
        self.path = path
        self.name = name
        self.function_list = dict()
        self.struct_list = dict()
        self.macro_list = dict()
        self.def_list = dict()
        self.decl_list = dict()
        self.enum_list = dict()
        self.type_def_list = dict()
        self.header_list = dict()
        self.definition_list = dict()
