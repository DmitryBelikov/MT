grammar GrammarParser;

ATTRIBUTE : '{' .*? '}';
WS : [ \t\n\r]+ -> skip;
COLON : ':';
SEMICOLON : ';';
UNION : '|';
EPS : 'EPS';
TOKEN_NAME : [A-Z] [a-zA-Z0-9_]*;
EXPR_NAME : [a-z] [a-zA-Z0-9_]*;
OTHER_SYMBOL : .;

regular_expr : (UNION | TOKEN_NAME | EXPR_NAME | OTHER_SYMBOL | EPS)+;
token : TOKEN_NAME COLON regular_expr SEMICOLON;

single_rule : EPS ATTRIBUTE | (TOKEN_NAME | EXPR_NAME)+ ATTRIBUTE;
rule_body : single_rule (UNION single_rule)*;
state_ : EXPR_NAME COLON rule_body SEMICOLON;

expr : token | state_;
result : expr+ EOF;