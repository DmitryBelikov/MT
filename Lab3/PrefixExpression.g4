grammar PrefixExpression;

WS : [ \t\r\n]+ -> skip;
PLUS : '+';
MINUS : '-';
MULTIPLY : '*';
DIVIDE : '/';
EQ : '==';
NOT_EQ : '!=';
LESS_EQ : '<=';
GREATER_EQ : '>=';
LESS : '<';
GREATER : '>';
ASSIGN : '=';
COMMA : ',';

AND : 'and';
OR : 'or';
NOT : 'not';
IF_ELSE : 'ifelse';
IF : 'if';
OUT : 'print';

VAR : [a-zA-Z_] [a-zA-Z_0-9]*;
NUMBER : '0' | [1-9][0-9]*;

var : VAR;
number : NUMBER;

operation : PLUS | MINUS | MULTIPLY | DIVIDE;
comp : EQ | NOT_EQ | LESS_EQ | GREATER_EQ | LESS | GREATER;

arithmetic : number | var | operation arithmetic arithmetic;
logic : comp arithmetic arithmetic | AND logic logic | OR logic logic | NOT logic;

if_ : IF logic prog;
ifelse_ : IF_ELSE logic prog prog;

assign : ASSIGN var arithmetic;
write : OUT arithmetic;

expr : arithmetic | logic | write | assign | if_ | ifelse_;
prog : expr | COMMA prog expr;
answer : prog EOF;
