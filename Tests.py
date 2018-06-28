# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 13:30:48 2018

@author: pedrobw
"""

import Project
import ASTcrochet

def test_parsing():
    path = "/media/pedrobw/6A384D7F384D4AF1/Users/Administrator/Examples/Backporting/Buffer_Overflow-Espruino/Pc/"
    project = Project.Project(path, "P")
    file = path + "targets/esp8266/esp8266_board_utils.c"
    ASTcrochet.parseAST(file, project)
    

def run():
    test_parsing()
    

if __name__=="__main__":
    run()