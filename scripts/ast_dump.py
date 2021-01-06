# Usage: python nsbug.py <file>

import sys
import clang.cindex


def indent(level):
    """ Indentation string for pretty-printing
    """
    return '  '*level


def output_cursor(cursor, level):
    """ Low level cursor output
    """
    spelling = ''
    displayname = ''

    if cursor.spelling:
        spelling = cursor.spelling
    if cursor.displayname:
        displayname = cursor.displayname
    kind = cursor.kind

    print(indent(level) + spelling, '<' + str(kind) + '>')
    print(indent(level+1) + '"'  + displayname + '"')


def output_cursor_and_children(cursor, level=0):
    """ Output this cursor and its children with minimal formatting.
    """
    output_cursor(cursor, level)
    if cursor.kind.is_reference():
        print(indent(level) + 'reference to:')
        output_cursor(clang.cindex.Cursor_ref(cursor), level+1)

    # Recurse for children of this cursor
    has_children = False
    for c in cursor.get_children():
        if not has_children:
            print(indent(level) + '{')
            has_children = True
        output_cursor_and_children(c, level+1)

    if has_children:
        print(indent(level) + '}')


index = clang.cindex.Index.create()
tu = index.parse(sys.argv[1], options=1)
output_cursor_and_children(tu.cursor)
