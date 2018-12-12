import sys
from antlr4 import *
from gen.PrefixExpressionLexer import PrefixExpressionLexer
from gen.PrefixExpressionParser import PrefixExpressionParser
from CustomVisitor import CustomVisitor
from CustomErrorListener import CustomErrorListener


def solve(expression):
    data_stream = InputStream(expression)
    lexer = PrefixExpressionLexer(data_stream)
    stream = CommonTokenStream(lexer)
    parser = PrefixExpressionParser(stream)
    parser._listeners = [CustomErrorListener()]
    try:
        tree = parser.answer()
    except SyntaxError as e:
        return str(e)
    visitor = CustomVisitor()
    return visitor.visit(tree)


def main(argv):
    input_file_name = argv[1]
    output_file_name = argv[2]
    with open(input_file_name) as input_file, open(output_file_name, 'w') as output_file:
        test = 0
        for line in input_file.readlines():
            test += 1
            result = solve(line)
            output_file.writelines('Test ' + str(test) + ': ' + line)
            output_file.writelines(result + '\n\n')


if __name__ == '__main__':
    main(sys.argv)
