import sys, ply.lex


reserved = {
    'define': 'DEFINE',
    'begin': 'BEGIN',
    'end': 'END',
    'each': 'EACH',
    'select': 'SELECT'
 }

tokens = ( 'LARROW', 'RARROW', 'LPAREN', 'RPAREN', 'LSQUARE', 'RSQUARE', 'COMMA',
            'DOT', 'PIPE', 'DOUBLEPLUS', 'DOUBLEMULT', 'DOUBLEDOT', 'COLON',
            'EQ', 'NOTEQ', 'LT', 'LTEQ', 'GT', 'GTEQ', 'PLUS', 'MINUS', 'MULT',
            'DIV', 'MOD', 'NUMBER_LITERAL', 'STRING_LITERAL', 'varIDENT',
            'constIDENT', 'tupleIDENT', 'funcIDENT', 'WHITESPACE',
            'NEWLINE', 'COMMENT', 'RES') + tuple(reserved.values())


t_LARROW = r'<-'
t_RARROW = r'->'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LSQUARE = r'\['
t_RSQUARE = r'\]'
t_COMMA = r','
t_DOT = r'\.'
t_PIPE = r'\|'
t_DOUBLEPLUS = r'\+\+'
t_DOUBLEMULT = r'\*\*'
t_DOUBLEDOT = r'\.\.'
t_COLON = r':'
t_EQ = r'='
t_NOTEQ = r'!='
t_LT = r'<'
t_LTEQ = r'<='
t_GT = r'>'
t_GTEQ = r'>='
t_PLUS  = r'\+'
t_MINUS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_MOD = r'%'


t_constIDENT = r'[A-Z]+'
t_funcIDENT = r'[A-Z][a-z0-9_]+'
t_ignore = ' \t\r'


def not_reserved(func):
    '''
    Decorator, that checks, whether matched string is within
    the list of reserved words. In case of a match, changes the type of
    token to the appropriate reserved value.
    @:param regex-function
    @:return function with ether original or edited regex
    '''

    is_reserved = False

    def wrapper(t):
        if t.value in reserved:
            nonlocal is_reserved
            is_reserved = True
            t.type = reserved[t.value]
        return t

    if is_reserved:
        # arbitrary regex that matched all the reserved words declared in specification
        wrapper.__doc__ = r'[a-z]+'
    else:
        wrapper.__doc__ = func.__doc__

    return wrapper



def t_STRING_LITERAL(t):
    r'\"([^\"]*)\"'
    t.value = t.value.strip('"')
    return t

def t_tupleIDENT(t):
    r'<[a-z]+>'
    t.value = t.value.strip('<>')
    return t

def t_NUMBER_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# a string that matches this regex can also be a reserved word,
# therefore marked by the decorator
@not_reserved
def t_varIDENT(t):
    r'[a-z]\w+'
    return t


'''
def t_RES(t):
    r'[a-z]+'
    if t.value in reserved:
        t.type = reserved[t.value]
    return t
'''

#########################################################
# Comments related stuff

states = (
    ('comment', 'exclusive'),
)

def t_comment(t):
    r'\{'
    t.lexer.comment_start = t.lexer.lexpos  # Record the starting position
    t.lexer.level = 1  # Initial brace level
    t.lexer.begin('comment')


def t_comment_lbrace(t):
    r'\{'
    t.lexer.level += 1


def t_comment_rbrace(t):
    r'\}'
    t.lexer.level -= 1

    if t.lexer.level == 0:
        t.lexer.begin('INITIAL')

def t_comment_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_comment_else(t):
    r'[^\n{}]+'
    pass


t_comment_ignore = ' \t\r'


def t_comment_error(t):
    raise Exception("Illegal character '{}' at line {}".format(
        t.value[0], t.lexer.lineno ) )


def t_comment_eof(t):
    if t.lexer.lexstate == 'comment':
        raise Exception("Unexpexted end of the file. Check the count of brackets")
    return None

#########################################################

def t_error(t):
    raise Exception("Illegal character '{}' at line {}".format(
        t.value[0], t.lexer.lineno ) )

# define lexer in module level so it can be used after
# importing this module:
lexer = ply.lex.lex()

# if this module/file is the first one started (the main module)
# then run:

def main():
    import argparse, codecs
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--who', action='store_true', help='name to print')
    group.add_argument('-f', '--file', help='filename to process')

    ns = parser.parse_args()

    if ns.who:
        # identify who wrote this
        print('276190, Magomed Udratov')

    elif ns.file is None:
        # user didn't provide input filename
        parser.print_help()
    else:
        # using codecs to make sure we process unicode
        with codecs.open(ns.file, 'r', encoding='utf-8') as INFILE:
            # blindly read all to memory (what if that is a 42Gb file?)
            # likely I am too lazy to write test files that big
            data = INFILE.read()

        lexer.input(data)

        while True:
            token = lexer.token()
            if token is None:
                break
            print(token)


if __name__ == '__main__':
    main()



