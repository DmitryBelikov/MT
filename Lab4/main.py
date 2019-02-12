import sys
from parser import Parser


def main(argv):
    grammar_file_name = argv[1]
    expression_file_name = argv[2]
    with open(expression_file_name) as file:
        expression = file.read()
    parser = Parser(grammar_file_name)
    result = parser.parse(expression)
    print("RESULT " + str(result.value))


if __name__ == '__main__':
    main(sys.argv)
