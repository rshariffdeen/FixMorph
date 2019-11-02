# -*- coding: utf-8 -*-

import os
from common.Utilities import error_exit, clean_files, execute_command
from tools import Emitter


class Project:
    
    def __init__(self, path, name):
        Emitter.information("creating project for " + path)
        if not (os.path.isdir(path)):
            error_exit(name + " is not an appropriate directory path.", path)
        if path[-1] != "/":
            path += "/"
        self.path = path
        self.name = name
        self.function_list = dict()
        self.struct_list = dict()
