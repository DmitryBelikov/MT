from collections import defaultdict
from re import *
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from gen.GrammarParserLexer import GrammarParserLexer
from gen.GrammarParserParser import GrammarParserParser
from gen.GrammarParserVisitor import GrammarParserVisitor


class CustomErrorListener(ErrorListener):
    def __init__(self):
        super(CustomErrorListener, self).__init__()

    def syntaxError(self, recognizer, offending_symbol, line, column, msg, e):
        raise SyntaxError("line " + str(line) + ":" + str(column) + " " + msg)


class CustomVisitor(GrammarParserVisitor):
    def __init__(self, parser):
        self.parser = parser

    def visitSingle_rule(self, ctx: GrammarParserParser.Single_ruleContext):
        attr = ctx.children[-1].getText()
        for referred in ctx.children[:-1]:
            self.parser.check_correctness(str(referred))
        return self.visitChildren(ctx)

    def visitResult(self, ctx: GrammarParserParser.ResultContext):
        for expr in ctx.children[:-1]:
            sibling = expr.children[0]
            if isinstance(sibling, GrammarParserParser.TokenContext):
                name = sibling.children[0].getText()
                regex = sibling.children[2].getText()
                self.parser.add_token(name, regex)
            if isinstance(sibling, GrammarParserParser.State_Context):
                name = sibling.children[0].getText()
                rules = sibling.children[2]
                for rule in rules.children[::2]:
                    self.parser.add_state(name, map(str, rule.children))
        return self.visitChildren(ctx)


EPS = 'EPS'
S = 's'
EOF = '$'


class Parser:

    def add_token(self, name, regex):
        if name in self.tokens:
            raise RuntimeError('Multiple definitions of ' + name)
        self.tokens[name] = compile(regex)

    def add_state(self, name, target):
        target = list(target)
        # if target[-1] != EPS:
        code = target.pop()[1:-1]
        if name not in self.states:
            self.states[name] = []
            self.codes[name] = []
        self.states[name].append(target)
        self.codes[name].append(code)
        # self.states[name].append((target, code))

    def check_correctness(self, name):
        if name == EPS:
            return
        if name not in self.tokens and name not in self.states:
            raise RuntimeError('Unknown token/rule: ' + name)

    def validate_start(self):
        if S not in self.states:
            raise RuntimeError('Start rule "' + S + '" is not defined')

    def validate_left_recursion(self):
        graph = {state : set() for state in self.states}
        for state, rules in self.states.items():
            for rule in rules:
                for item in rule:
                    if item == EPS:
                        continue
                    if item not in self.states:
                        break
                    if item not in graph[state]:
                        graph[state].add(item)
                    if [EPS] not in rules:
                        break

        def dfs(v, visited):
            if v in visited:
                raise RuntimeError("Left recursion in state " + v)
            visited.add(v)
            for child in graph[v]:
                dfs(child, visited)

        for start in graph:
            visited = set()
            dfs(start, visited)

    def validate_right_branching(self):
        for state in self.states:
            for i in range(len(self.states[state])):
                rule1 = self.states[state][i]
                for rule2 in self.states[state][(i + 1):]:
                    if rule1[0] == rule2[0]:
                        raise RuntimeError("Right branching occured in state " + state)

    def validate(self):
        self.validate_start()
        self.validate_left_recursion()
        self.validate_right_branching()

    def get_first(self, entities):
        result = set()
        for entity in entities:
            if entity not in self.states:
                result.add(entity)
                return result
            result.update(self.first[entity] - {EPS})
            if EPS not in self.states[entity]:
                return result
        result.add(EPS)
        return result

    def construct_first(self):
        for state in self.states:
            self.first[state] = set()
        changed = True
        while changed:
            changed = False
            for state in self.states:
                rules = zip(self.states[state], self.codes[state])
                prev_set = self.first[state].copy()
                for rule, code in rules:
                    self.first[state].update(self.get_first(rule))
                if prev_set != self.first[state]:
                    changed = True

    def construct_follow(self):
        changed = True
        self.follow[S].add(EOF)
        while changed:
            changed = False
            for state in self.states:
                rules_code = list(zip(self.states[state], self.codes[state]))
                for rule_code in rules_code:
                    rule = rule_code[0]
                    for i in range(len(rule)):
                        b = rule[i]
                        if b not in self.states:
                            continue
                        prev_set = self.follow[b].copy()
                        update_set = self.get_first(rule[i + 1:])
                        self.follow[b].update(update_set - {EPS})
                        if EPS in update_set:
                            self.follow[b].update(self.follow[state])
                        if prev_set != self.follow[b]:
                            changed = True

    def construct_rules(self):
        def start_with(token, states, codes):
            def is_start_with(token, rule):
                for entity in rule:
                    if entity == EPS:
                        continue
                    if entity == token:
                        return True
                    elif entity in self.tokens:
                        return False
                    elif token in self.first[entity]:
                        return True
                    elif EPS in self.first[entity]:
                        continue
                    else:
                        return False
                return False

            for rule, code in zip(states, codes):
                if is_start_with(token, rule):
                    return rule, code
            return [], ''
            # return [rule for rule in rules if is_start_with(token, rule)]

        for state in self.states:
            self.rules[state] = {token : start_with(token, self.states[state], self.codes[state]) for token in self.tokens}
            self.rules[state] = dict(filter(lambda tpl: tpl[1][0] != [], self.rules[state].items()))
            if EPS in self.first[state]:
                for rule, code in zip(self.states[state], self.codes[state]):
                    if rule == [EPS]:
                        eps_code = code
                self.rules[state][''] = ([EPS], eps_code) # {'' : ([EPS], eps_code)}

    def __init__(self, file):
        self.tokens = {}
        self.states = {}
        self.codes = {}
        self.first = {}
        self.follow = defaultdict(lambda: set())
        self.rules = {}

        lexer = GrammarParserLexer(FileStream(file))
        stream = CommonTokenStream(lexer)
        parser = GrammarParserParser(stream)
        parser._listeners = [CustomErrorListener()]

        tree = parser.result()
        visitor = CustomVisitor(self)
        visitor.visit(tree)

        self.validate()
        self.construct_first()
        self.construct_follow()
        self.construct_rules()

    def get_tokens(self, expr):
        tokens = []
        cur_pos = 0
        while cur_pos != len(expr):
            success = False
            for token, regex in self.tokens.items():
                result = regex.match(expr, cur_pos)
                if result is None:
                    continue
                success = True
                cur_pos = result.end()
                tokens.append((token, expr[result.start():result.end()]))
                break
            if not success:
                raise RuntimeError('Unable to match any token on position ' + str(cur_pos))
        tokens.append((EOF, ''))
        return tokens

    def construct_tree(self, tokens):
        def substitute_children(code):
            return sub(r'\$([0-9]+)', r'children[\1]', code)

        class SynthAttr:
            @staticmethod
            def wrap_code(code):
                wrapped = 'def my_func(children):\n\t' + '\n\t'.join(code.split('\n'))
                return wrapped

            @staticmethod
            def assign():
                return 'my_func(children_attrs)'

            def __init__(self, str_rep='', children_attrs=[], code=''):
                if code == '':
                    self.value = str_rep
                    return

                code = substitute_children(code)
                runnable_code = self.wrap_code(code)

                exec(runnable_code)
                self.value = eval(self.assign())

        class Accumulator:
            def __init__(self):
                self.pos = 0

            def next_token(self):
                self.pos += 1

        def update(accum, v):
            if v not in self.states:
                accum.next_token()

        def dfs(v, accum):
            cur_token = tokens[accum.pos][0]
            if v not in self.states:
                if cur_token != v:
                    raise ValueError('Parse error at position ' + str(accum.pos))
                update(accum, v)
                return SynthAttr(str_rep=tokens[accum.pos - 1][1])

            if cur_token in self.rules[v]:
                code = self.rules[v][cur_token][1]
                results = []
                for child in self.rules[v][cur_token][0]:
                    results.append(dfs(child, acc))
                update(accum, v)
                return SynthAttr(children_attrs=results, code=code)
            elif cur_token in self.follow[v]:
                return SynthAttr(code=self.rules[v][''][1])
            else:
                raise ValueError('Parse error at position ' + str(accum.pos))

        acc = Accumulator()
        return dfs(S, acc)

    def parse(self, expr):
        tokens = self.get_tokens(expr)
        return self.construct_tree(tokens)
