from ply import yacc
import tokenizer
import tree_print
import sys, os, traceback


class ASTnode:
    def __init__(self, typestr):
        self.nodetype = str(typestr)

    def __str__(self):
        if hasattr(self, "eval"):
            return str(self.eval) + " , params: " + str(self.params)
        elif hasattr(self, "value"):
            return str(self.value)
        else:
            return self.nodetype


# tokens are defined in lex-module, but needed here also in syntax rules
tokens = tokenizer.tokens


def p_program1(p):
    '''program : return_value DOT'''

    p[0] = ASTnode('program')
    p[0].children_definitions = []
    p[0].child_returns = p[1]


def p_program2(p):
    '''program : function_or_variable_definition program'''

    p[0] = p[2]
    p[0].children_definitions.append(p[1])



def p_function_or_variable_definition(p):
    '''function_or_variable_definition  : function_definition
                                        | variable_definitions'''
    p[0] = p[1]


def p_function_definition(p):
    '''function_definition  : DEFINE funcIDENT function_middle return_value DOT END DOT'''

    p[0] = ASTnode("function")
    p[0].child_identifier = ASTnode(p[2])
    p[0].children_definitions = p[3].definitions
    for defin in p[0].children_definitions:
        defin.scope = p[2]

    p[0].args = p[3].args if hasattr(p[3], "args") else []
    p[0].child_return = p[4]

    p[0].scope = "global"
    p[4].scope = p[2]


def p_function_middle1(p):
    '''function_middle : LSQUARE RSQUARE BEGIN'''
    p[0] = ASTnode("func_body")
    p[0].definitions = []

def p_function_middle2(p):
    '''function_middle : LSQUARE formals RSQUARE BEGIN'''
    p[0] = ASTnode("func_body")
    p[0].definitions = []
    p[0].args = p[2].identifiers

def p_function_middle3(p):
    '''function_middle : function_middle variable_definitions'''
    p[0] = p[1]
    p[0].definitions.append(p[2])


def p_formals1(p):
    '''formals  : varIDENT'''
    p[0] = ASTnode("formals")
    p[0].identifiers = [p[1]]


def p_formals2(p):
    '''formals  : formals COMMA varIDENT'''
    p[0] = p[1]
    p[0].identifiers.append(p[3])


def p_return_value(p):
    '''return_value  : EQ simple_expression
                     | NOTEQ pipe_expression'''

    p[0] = ASTnode("return_value")

    if p[2].nodetype == "evaluable":
        p[0].eval = p[2].eval
        a = p[2].params
        p[0].params = p[2].params

    else:
        p[0].value = p[2].value

    p[0].sign = p[1]
    p[0].scope = "global"

    if hasattr(p[2], "args"):
        p[0].args = p[2].args


def p_variable_definitions(p):
    '''variable_definitions  : varIDENT LARROW simple_expression DOT
                            | constIDENT LARROW constant_expression DOT
                            | tupleIDENT LARROW tuple_expression DOT
                            | pipe_expression RARROW tupleIDENT DOT'''


    var_type = p.slice[1].type

    if var_type == 'pipe_expression':
        print('tuplevariable_definition( {} )'.format(p[3]))
        p[0] = ASTnode("Tuple")
        p[0].child_identifier = ASTnode(p[3])
        p[0].child_value = p[1]

    else:
        p[0] = ASTnode("definition")

        if var_type == 'varIDENT':
            p[0] = ASTnode("variable")

        elif var_type == 'constIDENT':
            p[0] = ASTnode("constant")

        elif var_type == 'tupleIDENT':
            p[0] = ASTnode("tuple")

        p[0].child_identifier = ASTnode(p[1])
        p[0].child_value = p[3]

    p[0].scope = "global"

def p_constant_expression1(p):
    '''constant_expression : NUMBER_LITERAL'''
    p[0] = ASTnode("constant_expression")
    p[0].value = p[1]

def p_constant_expression2(p):
    '''constant_expression : constIDENT'''
    identifier = p[1]
    p[0] = ASTnode("evaluable")
    p[0].eval = lambda **kwargs: kwargs.pop(identifier)
    p[0].params = [identifier]


def p_pipe_expression(p):
    '''pipe_expression  : pipe_expression PIPE pipe_operation
                        | tuple_expression'''

    if p.slice[1].type == 'tuple_expression':
        print('pipe_expression')
        p[0] = p[1]
    else:
        p[0] = ASTnode("Pipe expression")
        p[0].children_operands = [p[1], p[3]]


def p_pipe_operation1(p):
    '''pipe_operation  : MULT
                       | PLUS'''
    p[0] = ASTnode(p[1])

def p_pipe_operation2(p):
    '''pipe_operation  : funcIDENT
                       | each_statement'''
    p[0] = ASTnode(p[1])


def p_each_statement(p):
    '''each_statement  : EACH COLON funcIDENT'''
    p[0] = p[3]


def p_tuple_expression1(p):
    '''tuple_expression  : tuple_atom'''
    p[0] = p[1]

def p_tuple_expression2(p):
    '''tuple_expression  : tuple_expression tuple_operation tuple_atom'''

    first = p[1]
    second = p[3]

    if first.nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        if second.nodetype == "evaluable":
            p[0].eval = lambda **kwargs: first.eval(**kwargs) + second.eval(**kwargs)
            p[0].params = p[1].params + p[3].params
        else:
            p[0].eval = lambda **kwargs: first.eval(**kwargs) + second.value
            p[0].params = p[1].params

    elif second.nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        p[0].eval = lambda **kwargs: first.value + second.eval(**kwargs)
        p[0].params = p[3].params

    else:
        p[0] = ASTnode("tuple_expression")
        try:
            p[0].value = first.value + second.value
        except Exception as e:
            p[0].error = e
            p[0].lineno = p.stack[-1].lineno

    p[0].children_components = []
    p[0].children_components.append(ASTnode(p[3]))
    p[0].children_components.append(p[1])


def p_tuple_operation(p):
    '''tuple_operation : DOUBLEPLUS'''


def p_tuple_atom4(p):
    '''tuple_atom  : function_call'''
    identifier = p[1]
    p[0] = ASTnode("evaluable")
    p[0].eval = lambda **kwargs: kwargs.pop(identifier)
    p[0].params = identifier.params
    p[0].args = p[1].args


def p_tuple_atom1(p):
    '''tuple_atom  : tupleIDENT'''
    identifier = p[1]
    p[0] = ASTnode("evaluable")
    p[0].eval = lambda **kwargs: kwargs.pop(identifier)
    p[0].params = [identifier]


def p_tuple_atom2(p):
    '''tuple_atom  : LSQUARE constant_expression DOUBLEMULT constant_expression RSQUARE
                   | LSQUARE constant_expression DOUBLEDOT  constant_expression RSQUARE'''

    first = p[2]
    second = p[4]

    if first.nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        if second.nodetype == "evaluable":
            if p[3] == "**":
                p[0].eval = lambda **kwargs: [second.eval(**kwargs)] * first.eval(**kwargs)
            else:
                p[0].eval = lambda **kwargs: [i for i in range(first.eval(**kwargs), second.eval(**kwargs) + 1)]
            p[0].params = p[1].params + p[3].params
        else:
            if p[3] == "**":
                p[0].eval = lambda **kwargs: [second.value] * first.eval(**kwargs)
            else:
                p[0].eval = lambda **kwargs: [i for i in range(first.eval(**kwargs), second.value + 1)]
            p[0].params = p[1].params
    elif second.nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        if p[3] == "**":
            p[0].eval = lambda **kwargs: [second.eval(**kwargs)] * first.value
        else:
            p[0].eval = lambda **kwargs: [i for i in range(first.value, second.value + 1)]

        p[0].params = p[3].params
    else:
        p[0] = ASTnode("range_expression")
        try:
            if p[3] == "**":
                p[0].value = [second.value] * first.value
            else:
                p[0].value = [i for i in range(first.value, second.value + 1)]

        except Exception as e:
            p[0].error = e
            p[0].lineno = p.stack[-1].lineno

    p[0].child_start = p[2]
    p[0].child_type = ASTnode(p[3])
    p[0].child_end = p[4]


def p_tuple_atom3(p):
    '''tuple_atom  : LSQUARE arguments RSQUARE'''
    if any(expr.nodetype == "evaluable" for expr in p[2].children_expressions):
        p[0] = ASTnode("evaluable")
        args = p[2].children_expressions
        p[0].eval = lambda **kwargs: [expr.eval(**kwargs) if expr.nodetype == "evaluable" else expr.value for expr in args]
        p[0].params = [param for expr in p[2].children_expressions if expr.nodetype == "evaluable" for param in expr.params]

    else:
        p[0] = ASTnode("list")
        p[0].value = [expr.value for expr in p[2].children_expressions]



def p_function_call(p):
    '''function_call : funcIDENT LSQUARE arguments RSQUARE
                     | funcIDENT LSQUARE RSQUARE'''

    p[0] = ASTnode("function_call")

    if len(p) == 5:
        p[0].args = p[3].children_expressions
        p[0].params = [p[1]] + [param for arg in p[3].children_expressions if hasattr(arg, "params") for param in arg.params]
        pars = p[0].params
    else:
        p[0].args = []
        p[0].eval = lambda **kwargs: p[1].eval(kwargs)
        p[0].params = [p[1]]
        pars = p[0].params

    p[0].identifier = p[1]


def p_arguments1(p):
    '''arguments : simple_expression'''
    p[0] = ASTnode("arguments")
    p[0].children_expressions = [p[1]]


def p_arguments2(p):
    '''arguments : arguments COMMA simple_expression'''
    p[0] = p[1]
    p[0].children_expressions.append(p[3])
 


def p_atom1(p):
    '''atom : NUMBER_LITERAL
            | STRING_LITERAL'''

    p[0] = ASTnode("atom")
    p[0].value = p[1]



def p_atom5(p):
    '''atom : function_call'''

    identifier = p[1]

    if not hasattr(p[1], "value"):
        p[0] = ASTnode("evaluable")
        p[0].eval = lambda **kwargs: kwargs.pop(identifier.identifier)
        p[0].params = identifier.params
    else:
        p[0] = ASTnode("atom")
        p[0].value = identifier.value

    p[0].args = p[1].args


def p_atom2(p):
    '''atom : varIDENT
            | constIDENT'''

    identifier = p[1]
    p[0] = ASTnode("evaluable")
    p[0].eval = lambda **kwargs: kwargs.pop(identifier)
    p[0].params = [identifier]


def p_atom3(p):
    '''atom : LPAREN simple_expression RPAREN'''

    if p[2].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        p[0].eval = p[2].eval
        p[0].params = p[2].params
    else:
        p[0] = ASTnode("atom")
        p[0].value = p[2].value

    if hasattr(p[2], "args"):
        p[0].args = p[2].args


def p_atom4(p):
    '''atom : SELECT COLON constant_expression LSQUARE tuple_expression RSQUARE'''
    p[0] = ASTnode("Atom")

    first = p[3]
    second = p[5]

    if first.nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        if second.nodetype == "evaluable":
            p[0].eval = lambda **kwargs: second.eval(**kwargs)[first.eval(**kwargs)-1]
            p[0].params = first.params + second.params
        else:
            p[0].eval = lambda **kwargs: second.value[first.eval(**kwargs)-1]
            p[0].params = first.params

    elif second.nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        p[0].eval = lambda **kwargs: second.eval(**kwargs)[first.value-1]
        p[0].params = second.params

    else:
        p[0] = ASTnode("tuple_expression")
        try:
            p[0].value = second.value[first.value-1]
        except Exception as e:
            p[0].error = e
            p[0].lineno = p.stack[-1].lineno

    p[0].child_index = p[3]
    p[0].child_container = p[5]



def p_factor(p):
    '''factor : MINUS atom
              | atom'''

    p[0] = ASTnode("factor")

    if len(p) == 3:
        if p[2].nodetype == "evaluable":
            p[0].nodetype = "evaluable"
            p[0].eval = lambda **kwargs: -1 * p[2].eval(**kwargs)
            p[0].params = p[2].params
        else:
            p[0].value = -1 * p[2].value

        if hasattr(p[2], "args"):
            p[0].args = p[1].args
    else:
        if p[1].nodetype == "evaluable":
            p[0].nodetype = "evaluable"
            p[0].eval = p[1].eval
            p[0].params = p[1].params
        else:
            p[0].value = p[1].value

        if hasattr(p[1], "args"):
            p[0].args = p[1].args



def p_term1(p):
    '''term : factor'''

    if p[1].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        p[0].eval = p[1].eval
        p[0].params = p[1].params
    else:
        p[0] = ASTnode("term")
        p[0].value = p[1].value

    if hasattr(p[1], "args"):
        p[0].args = p[1].args



def p_term2(p):
    '''term : term MULT factor
            | term DIV factor'''

    first = p[1]
    second = p[3]

    if hasattr(p[3], "error"):
        p[0] = ASTnode("term")
        p[0].error = second.error

    elif p[1].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")

        if second.nodetype == "evaluable":

            if p[2] == "*":
                p[0].eval = lambda **kwargs: first.eval(**kwargs) * second.eval(**kwargs)
            else:
                p[0].eval = lambda **kwargs: first.eval(**kwargs) / second.eval(**kwargs)

            p[0].params = first.params + second.params

        else:
            if p[2] == "*":
                p[0].eval = lambda **kwargs: first.eval(**kwargs) * second.value
            else:
                p[0].eval = lambda **kwargs: first.eval(**kwargs) / second.value

            p[0].params = first.params

    elif p[3].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")

        if p[2] == "*":
            p[0].eval = lambda **kwargs: first.value * second.eval(**kwargs)
        else:
            p[0].eval = lambda **kwargs: first.value / second.eval(**kwargs)

        p[0].params = p[3].params

    else:
        p[0] = ASTnode("term")

        try:
            p[0].value = eval(str(p[1]) + p[2] + str(p[3]))
        except Exception as e:
            p[0].error = e
            p[0].lineno = p.stack[-1].lineno

    sign = ASTnode("op")
    sign.value = p[2]
    p[0].children_operands = [p[1], sign, p[3]]


def p_simple_expression1(p):
    '''simple_expression  : term'''

    if p[1].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")
        p[0].eval = p[1].eval
        p[0].params = p[1].params
    else:
        p[0] = ASTnode("simple_expression")
        p[0].value = p[1].value

    if hasattr(p[1], "args"):
        p[0].args = p[1].args


def p_simple_expression2(p):
    '''simple_expression  : term PLUS simple_expression
                          | term MINUS simple_expression'''

    first = p[1]
    second = p[3]

    if hasattr(p[3], "error"):
        p[0] = ASTnode("simple_expression")
        p[0].error = second.error

    elif p[1].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")


        if p[3].nodetype == "evaluable":
            if p[2] == "+":

                p[0].eval = lambda **kwargs: first.eval(**kwargs) + second.eval(**kwargs)
            else:
                p[0].eval = lambda **kwargs: first.eval(**kwargs) - second.eval(**kwargs)

            p[0].params = first.params + second.params

        else:
            if p[2] == "+":
                p[0].eval = lambda **kwargs: first.eval(**kwargs) + second.value
            else:
                p[0].eval = lambda **kwargs: first.eval(**kwargs) - second.value

            p[0].params = first.params

    elif p[3].nodetype == "evaluable":
        p[0] = ASTnode("evaluable")

        if p[2] == "+":
            p[0].eval = lambda **kwargs: first.value + second.eval(**kwargs)
        else:
            p[0].eval = lambda **kwargs: first.value - second.eval(**kwargs)

        p[0].params = second.params

    else:
        p[0] = ASTnode("simple_expression")

        try:
            if type(second.value) is str:
                res = first.value + second.value if p[2] == "+" else first.value - second.value
            else:
                res = eval(str(first) + p[2] + str(second))
        except Exception as e:
            p[0].error = e
            p[0].lineno = p.stack[-1].lineno

        else:
            p[0].value = res

    sign = ASTnode("op")
    sign.value = p[2]
    p[0].children_operands = [first, sign, second]

    if hasattr(p[1], "args"):
        p[0].args = p[1].args

    if hasattr(p[3], "args"):
        if hasattr(p[1], "args"):
            p[0].args += p[3].args
        else:
            p[0].args = p[3].args


def p_error(p):
    print( 'syntax error @', p )
    raise SystemExit


parser = yacc.yacc()


if __name__ == '__main__':
    import argparse, codecs
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-t', '--treetype', help='type of output tree (unicode/ascii/dot)')
    group = arg_parser.add_mutually_exclusive_group()
    group.add_argument('--who', action='store_true', help='who wrote this' )
    group.add_argument('-f', '--file', help='filename to process')
    ns = arg_parser.parse_args()

    outformat = "dot"
    if ns.treetype:
        outformat = ns.treetype

    if ns.file is None:
        ns.file = "exs/04_semantics_run_examples_run_level4_test1.tupl"


    if ns.who == True:
        # identify who wrote this
        print( '276190 Magomed Udratov' )

    elif ns.file is None:
        # user didn't provide input filename
        arg_parser.print_help()
    else:
        data = codecs.open( ns.file, encoding='utf-8' ).read()
        result = parser.parse(data, lexer=tokenizer.lexer, debug=False)
        if result is None:
            print( 'syntax OK' )

        print("\n\n")

        tree_print.treeprint(result, outformat)

