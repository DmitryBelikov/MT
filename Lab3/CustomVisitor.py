from gen.PrefixExpressionParser import PrefixExpressionParser
from gen.PrefixExpressionVisitor import ParseTreeVisitor


# This class defines a complete generic visitor for a parse tree produced by PrefixExpressionParser.
class CustomVisitor(ParseTreeVisitor):
    @staticmethod
    def add_tabs(expr):
        return '\n'.join(map(lambda s: '\t' + s, expr.split('\n')))

    @staticmethod
    def multi_match(test_list, pattern):
        if len(test_list) != len(pattern):
            return False
        return all(isinstance(elem, t) for (elem, t) in zip(test_list, pattern))

    def visitNumber(self, ctx:PrefixExpressionParser.NumberContext):
        return ctx.getText()

    # Visit a parse tree produced by PrefixExpressionParser#var.
    def visitVar(self, ctx: PrefixExpressionParser.VarContext):
        return ctx.getText()

    # Visit a parse tree produced by PrefixExpressionParser#operation.
    def visitOperation(self, ctx: PrefixExpressionParser.OperationContext):
        return ctx.getText()

    # Visit a parse tree produced by PrefixExpressionParser#comp.
    def visitComp(self, ctx: PrefixExpressionParser.CompContext):
        return ctx.getText()

    # Visit a parse tree produced by PrefixExpressionParser#arithmetic.
    def visitArithmetic(self, ctx: PrefixExpressionParser.ArithmeticContext):
        children = ctx.children
        if CustomVisitor.multi_match(children, [PrefixExpressionParser.OperationContext, PrefixExpressionParser.ArithmeticContext, PrefixExpressionParser.ArithmeticContext]):
            operation, left, right = children
            return '({1}) {0} ({2})'.format(self.visitOperation(operation), self.visitArithmetic(left), self.visitArithmetic(right))
        elif CustomVisitor.multi_match(children, [PrefixExpressionParser.VarContext]):
            return self.visitVar(children[0])
        else:
            return self.visitNumber(children[0])

    # Visit a parse tree produced by PrefixExpressionParser#logic.
    def visitLogic(self, ctx: PrefixExpressionParser.LogicContext):
        children = ctx.children
        first = children[0]
        if CustomVisitor.multi_match(children, [PrefixExpressionParser.CompContext, PrefixExpressionParser.ArithmeticContext, PrefixExpressionParser.ArithmeticContext]):
            comp, arg1, arg2 = children
            return '({1}) {0} ({2})'.format(self.visitComp(comp), self.visitArithmetic(arg1), self.visitArithmetic(arg2))
        elif str(first) == 'not':
            return 'not ({0})'.format(self.visitLogic(children[1]))
        else:
            arg1, arg2 = children[1:]
            operation = str(first)
            return '({1}) {0} ({2})'.format(operation, self.visitLogic(arg1), self.visitLogic(arg2))

    # Visit a parse tree produced by PrefixExpressionParser#if_.
    def visitIf_(self, ctx: PrefixExpressionParser.If_Context):
        condition, prog = ctx.children[1:]

        condition_code = self.visitLogic(condition)
        prog_code = CustomVisitor.add_tabs(self.visitProg(prog))

        return 'if {0}:\n{1}'.format(condition_code, prog_code)

    # Visit a parse tree produced by PrefixExpressionParser#ifelse_.
    def visitIfelse_(self, ctx: PrefixExpressionParser.Ifelse_Context):
        condition, true_prog, false_prog = ctx.children[1:]

        condition_code = self.visitLogic(condition)
        true_code = CustomVisitor.add_tabs(self.visitProg(true_prog))
        false_code = CustomVisitor.add_tabs(self.visitProg(false_prog))

        return 'if {0}:\n{1}\nelse:\n{2}'.format(condition_code, true_code, false_code)

    # Visit a parse tree produced by PrefixExpressionParser#assign.
    def visitAssign(self, ctx: PrefixExpressionParser.AssignContext):
        var, arithmetic = ctx.children[1:]
        return '{0} = {1}'.format(self.visitVar(var), self.visitArithmetic(arithmetic))

    # Visit a parse tree produced by PrefixExpressionParser#write.
    def visitWrite(self, ctx: PrefixExpressionParser.WriteContext):
        return 'print({0})'.format(self.visitArithmetic(ctx.children[1]))

    # Visit a parse tree produced by PrefixExpressionParser#expr.
    def visitExpr(self, ctx: PrefixExpressionParser.ExprContext):
        children = ctx.children
        child = children[0]
        if CustomVisitor.multi_match(children, [PrefixExpressionParser.ArithmeticContext]):
            return self.visitArithmetic(child)
        elif CustomVisitor.multi_match(children, [PrefixExpressionParser.LogicContext]):
            return self.visitLogic(child)
        elif CustomVisitor.multi_match(children, [PrefixExpressionParser.WriteContext]):
            return self.visitWrite(child)
        elif CustomVisitor.multi_match(children, [PrefixExpressionParser.AssignContext]):
            return self.visitAssign(child)
        elif CustomVisitor.multi_match(children, [PrefixExpressionParser.If_Context]):
            return self.visitIf_(child)
        else:
            return self.visitIfelse_(child)

    # Visit a parse tree produced by PrefixExpressionParser#prog.
    def visitProg(self, ctx: PrefixExpressionParser.ProgContext):
        children = ctx.children
        if CustomVisitor.multi_match(children, [PrefixExpressionParser.ExprContext]):
            return self.visitExpr(children[0])
        return '{0}\n{1}'.format(self.visitProg(children[1]), self.visitExpr(children[2]))

    def visitAnswer(self, ctx:PrefixExpressionParser.AnswerContext):
        return self.visitProg(ctx.children[0])