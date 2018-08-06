#! /usr/bin/env python3
# -*- coding: utf-8 -*-

Pa = None
Pb = None
Pc = None
crash_script = None

CONF_FILE_NAME = "crochet.conf"
PATCH_COMMAND = "crochet-patch"
PATCH_SIZE = "1000"
DIFF_SIZE = "crochet-diff "
DIFF_COMMAND = "1000"
SYNTAX_CHECK_COMMAND = "clang-check "
STYLE_FORMAT_COMMAND = "clang-format -style=LLVM "

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

UPDATEMOVE = "UpdateMove"
UPDATE = "Update"
MOVE = "Move"
INSERT = "Insert"
DELETE = "Delete"
MATCH = "Match"
TO = " to "
AT = " at "
INTO = " into "
AND = "and"
order = [UPDATE, UPDATEMOVE, DELETE, MOVE, INSERT]


patch_for_header_files = []
patch_for_header_files = []