#!/usr/bin/env python3
#

from semantics_common import SymbolData, SemData, create_scope


def eval_var_value(node, semdata):
    kwargs = {key: semdata.symtbl[node.scope]["value"].get(key) for key in node.child_value.params}
    node.child_value.value = node.child_value.eval(**kwargs)
    semdata.symtbl[node.scope]["value"][node.child_identifier.nodetype] = node.child_value.value


def eval_var_node(node, semdata):
    if node.scope not in semdata.symtbl:
        create_scope(semdata, node.scope)

    if not hasattr(node.child_value, "value"):
        if all(param in semdata.symtbl[node.scope]["value"] for param in node.child_value.params):
            eval_var_value(node, semdata)
        else:
            semdata.symtbl[node.scope]["no_value"].add(node)
    else:
        semdata.symtbl[node.scope]["value"][node.child_identifier.nodetype] = node.child_value.value


def re_eval_vars(semdata, scope="global"):
    evaluated = []

    iters, size = 0, 0
    while size > 0:
        for node in semdata.symtbl[scope]["no_value"]:
            if eval_var_node(node, semdata):
                evaluated.append(node)
        semdata.symtbl[scope]["no_value"].difference_update(evaluated)
        evaluated = []
        size = len(semdata.symtbl[scope]["no_value"])
        iters += 1

        if iters > 5:
            raise RuntimeError("Couldn't evaluate all the variables")


def print_vars(semdata):
    if semdata.stack and type(semdata.stack[-1]) is dict:

        for node in semdata.stack[-1]["var_data"]["novalue"]:
            eval_var_node(node, semdata)

        for key, value in semdata.stack[-1]["var_data"]["value"].items():
            print(key, ":", value)


def run_program(tree, semdata):
    semdata.old_stacks = []
    semdata.stack = []
    eval_node(tree, semdata)


def eval_func(node, semdata):
    for param in node.params:
        if param in semdata.symtbl["functions"]:
            kwargs = {}

            for no_value_node in semdata.symtbl[param]["no_value"]:
                for index, func_arg in enumerate(semdata.symtbl["functions"][param]["args"]):
                    if func_arg in no_value_node.child_value.params:
                        argum = node.args[index] if node.args[index] != param else node.args[index+1]
                        if not hasattr(argum, "value"):
                            kwars = {key: semdata.symtbl[node.scope]["value"].get(key) for key in
                                      argum.params}
                            argum.value = argum.eval(**kwars)
                        kwargs[func_arg] = argum.value

                no_value_node.child_value.value = no_value_node.child_value.eval(**kwargs)
                semdata.symtbl[no_value_node.scope]["value"][no_value_node.child_identifier.nodetype] = no_value_node.child_value.value

            return_node = semdata.symtbl["functions"][param]["return"]

            for index, func_arg in enumerate(semdata.symtbl["functions"][param]["args"]):
                if func_arg in return_node.params:
                    argum = node.args[index] if node.args[index] != param else node.args[index + 1]
                    if not hasattr(argum, "value"):
                        kwars = {key: semdata.symtbl[node.scope]["value"].get(key) for key in
                                 argum.params}
                        argum.value = argum.eval(**kwars)
                    kwargs[func_arg] = argum.value

            for key in set(return_node.params):
                if key not in kwargs or kwargs[key] is None:
                    kwargs[key] = semdata.symtbl["global"]["value"].get(key)
                    kwargs[key] = semdata.symtbl[node.scope]["value"].get(key) or kwargs[key]
                    kwargs[key] = semdata.symtbl[return_node.scope]["value"].get(key) or kwargs[key]

            node.value = return_node.eval(**kwargs)


def eval_node(node, semdata):
    symtbl = semdata.symtbl
    nodetype = node.nodetype
    s = 0

    if nodetype == 'program':
        # Copy and store current stack
        semdata.old_stacks.append(semdata.stack.copy())
        for i in node.children_definitions:
          eval_node(i, semdata)
        eval_node(node.child_returns, semdata)
        # Restore stack
        semdata.stack = semdata.old_stacks.pop()
        return None

    elif nodetype == "variable" or nodetype == "constant" or nodetype == "tuple":
        eval_var_node(node, semdata)

    elif nodetype == "function":
        if "functions" not in symtbl:
            symtbl["functions"] = {}

        if node.child_identifier.nodetype not in semdata.symtbl:
            create_scope(semdata, node.child_identifier.nodetype)

        symtbl["functions"][node.child_identifier.nodetype] = {"defs" : node.children_definitions,
                                                               "return" : node.child_return,
                                                               "args" : node.args, }

        for i in node.children_definitions:
            eval_node(i, semdata)

    elif nodetype == 'return_value':
        if not hasattr(node, "value"):
            if any(key not in symtbl[node.scope]["value"] for key in node.params) and hasattr(node, "args"):
                eval_func(node, semdata)
            elif all(key in symtbl[node.scope]["value"] for key in node.params):
                re_eval_vars(semdata)
                kwargs = {key: semdata.symtbl[node.scope]["value"].get(key) for key in node.params}
                node.value = node.eval(**kwargs)

        print("Return value of the program:", node.value)





import sys
import tokenizer
import tree_generation
import tree_print
parser = tree_generation.parser

import semantics_check

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

        semdata = SemData()
        semdata.in_function = None
        tree_print.treeprint(ast_tree)
        print("Semantics ok.")
        create_scope(semdata, "global")
        semdata.symtbl["global"]["declared"] = set()
        semdata.symtbl["global"]["functions"] = dict()

        semantics_check.semantic_checks(ast_tree, semdata)
        run_program(ast_tree, semdata)
        print("Program finished.")
