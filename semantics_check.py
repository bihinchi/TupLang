#!/usr/bin/env python3
#
import sys
from semantics_common import visit_tree, SymbolData, SemData, create_scope

# Define semantic check functions



def check_everything(node, semdata):

    nodetype = node.nodetype

    if hasattr(node, "error"):
        return node.error

    if nodetype == "variable" :
        if node.scope not in semdata.symtbl:
            create_scope(semdata, node.scope)
            semdata.symtbl[node.scope]["declared"] = set()

        semdata.symtbl[node.scope]["declared"].add(node.child_identifier.nodetype)
        if node.child_value.nodetype == "evaluable":
            for var in node.child_value.params:
                if var not in semdata.symtbl[node.scope]["declared"] and var not in semdata.symtbl["global"]["declared"]:
                    return "Referencing '" + var + "' that was not declared"

    if nodetype == "constant" or nodetype == "tuple":
        if node.scope not in semdata.symtbl:
            create_scope(semdata, node.scope)
            semdata.symtbl[node.scope]["declared"] = set()

        if node.child_identifier.nodetype in semdata.symtbl[node.scope]["declared"]:
            return node.child_identifier.nodetype + "' cannot be defined again"

        semdata.symtbl[node.scope]["declared"].add(node.child_identifier.nodetype)
        if node.child_value.nodetype == "evaluable":
            for var in node.child_value.params:
                if var not in semdata.symtbl[node.scope]["declared"] and var not in semdata.symtbl["global"]["declared"]:
                    return "Referencing '" + var + "' that was not declared"

    if nodetype == "function":
        if node.child_return.scope not in semdata.symtbl:
            create_scope(semdata, node.child_return.scope)
            semdata.symtbl[node.child_identifier.nodetype]["declared"] = set()

        semdata.symtbl["global"]["functions"][node.child_identifier.nodetype] = len(node.args)

        if node.child_identifier.nodetype in semdata.symtbl[node.scope]["declared"]:
            return "Function '" + node.child_identifier.nodetype + "' is already declared"

        semdata.symtbl[node.scope]["declared"].add(node.child_identifier.nodetype)
        [semdata.symtbl[node.child_identifier.nodetype]["declared"].add(ident) for ident in node.args]

    if nodetype == "return_value":
        if not hasattr(node, "value"):
            for param in node.params:
                if param not in semdata.symtbl[node.scope]["declared"] and param not in semdata.symtbl["global"]["declared"]:
                    return "Referencing '" + param + "' that was not declared"


    if nodetype != "function" and hasattr(node, "args"):
        func_found = False
        for param in node.params:
            if param in semdata.symtbl["global"]["functions"]:
                func_found = True
                if len(node.args) != semdata.symtbl["global"]["functions"][param]:
                    return "Number of parameters do not match when calling '" + param + "'"

        if not func_found:
            return "Calling unknown function"



def semantic_checks(tree, semdata):
  '''run all semantic checks'''
  semdata.stack = []
  semdata.stack_size = 0 # Initially stack is empty
  semdata.old_stack_sizes = [] # Initially no old stacks
  visit_tree(tree, check_everything, None, semdata)


import tokenizer
import tree_generation
import tree_print
parser = tree_generation.parser

if __name__ == "__main__":
    import argparse, codecs
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-f', '--file', help='filename to process')

    ns = arg_parser.parse_args()

    if ns.file is None:
        arg_parser.print_help()
    else:
        data = codecs.open( ns.file, encoding='utf-8' ).read()
        ast_tree = parser.parse(data, lexer=tokenizer.lexer, debug=False)
        ast_tree.children_definitions.reverse()
        tree_print.treeprint(ast_tree)

        semdata = SemData()
        semdata.in_function = None
        semdata.symtbl = {}

        create_scope(semdata, "global")
        semdata.symtbl["global"]["declared"] = set()
        semdata.symtbl["global"]["functions"] = dict()


        semantic_checks(ast_tree, semdata)
        print("Semantics ok:")
