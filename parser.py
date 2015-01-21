import ply.lex as lex

tokens = (
	'NAME', 'SELECT', 'VERSION'
)

# Tokens

t_NAME    = r'[a-zA-Z_=-][a-zA-Z0-9_=-]*'
t_SELECT  = r'\(.*\)'
t_VERSION = r'\d+.*'

t_ignore = " \t"

def t_newline(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")

def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

lex.lex()

def p_error(p):
	if p:
		print("Syntax error at '%s'" % p.value)
		raise SyntaxError("Syntax error at '%s'" % p.value)
	else:
		print("Syntax error at EOF")
		raise SyntaxError("Syntax error at EOF")

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
