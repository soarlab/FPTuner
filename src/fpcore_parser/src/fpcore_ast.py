

from fpcore_lexer import FPCoreLexer
from fpcore_logging import Logger

import sys


logger = Logger()


def list_to_str(l, sep=" "):
    return sep.join([str(i) for i in l])


def list_to_repr(l):
    return ", ".join([repr(i) for i in l])


# +---------------------------------------------------------------------------+
# | ASTNode                                                                   |
# +---------------------------------------------------------------------------+
class ASTNode:
    def __init__(self):
        pass

    def __str__(self):
        class_name = type(self).__name__
        msg = "__str__ is not defined for {}".format(class_name)
        raise NotImplementedError(msg)

    def __repr__(self):
        class_name = type(self).__name__
        return "{}({{}})".format(class_name)


# +---------------------------------------------------------------------------+
# | Expr                                                                      |
# +---------------------------------------------------------------------------+
class Expr(ASTNode):
    def __init__(self):
        super().__init__()
        self.properties = list()

    def add_properties(self, properties):
        self.properties.extend(properties)
        return self

    def __str__(self):
        if len(self.properties) == 0:
            return "{}"
        return "(! {} {{}})".format(list_to_str(self.properties))

    def __repr__(self):
        format_repr = super().__repr__()
        if len(self.properties) == 0:
            return format_repr
        props = list_to_repr(self.properties)
        prop_repr = ".add_properites([{}])".format(props)
        return format_repr + prop_repr


# +---------------------------------------------------------------------------+
# | Atoms                                                                     |
# +---------------------------------------------------------------------------+
class Atom(Expr):
    def __init__(self, source):
        super().__init__()
        self.source = source

    def __str__(self):
        format_str = super().__str__()
        return format_str.format(self.source)

    def __repr__(self):
        format_repr = super().__repr__()
        return format_repr.format(repr(self.source))


class Number(Atom):
    pass


class Constant(Atom):
    pass


class Variable(Atom):
    pass


# +---------------------------------------------------------------------------+
# | Operations                                                                |
# +---------------------------------------------------------------------------+
class Operation(Expr):
    def __init__(self, op, *args):
        super().__init__()
        if len(args) == 1 and op not in FPCoreLexer.UNARY_OPERATIONS:
            logger.error("Operation '{}' is not unary, given: {}", op, args)
            logger.error("Possible unary operations:\n{}",
                         "\n".join(sorted(FPCoreLexer.UNARY_OPERATIONS)))
            sys.exit(1)

        elif len(args) == 2 and op not in FPCoreLexer.BINARY_OPERATIONS:
            logger.error("Operation '{}' is not binary, given: {}", op, args)
            logger.error("Possible binary operations:\n{}",
                         "\n".join(sorted(FPCoreLexer.BINARY_OPERATIONS)))
            sys.exit(1)

        elif len(args) == 3 and op not in FPCoreLexer.TERNARY_OPERATIONS:
            logger.error("Operation '{}' is not ternary, given: {}", op, args)
            logger.error("Possible ternary operations:\n{}",
                         "\n".join(sorted(FPCoreLexer.TERNARY_OPERATIONS)))
            sys.exit(1)

        elif len(args) >= 4 and op not in FPCoreLexer.NARY_OPERATIONS:
            logger.error("Operation '{}' is not n-ary, given: {}", op, args)
            logger.error("Possible n-ary operations:\n{}",
                         "\n".join(sorted(FPCoreLexer.NARY_OPERATIONS)))
            sys.exit(1)

        self.op = op
        self.args = args

    def __str__(self):
        format_str = super().__str__()
        this_str = "({} {})".format(self.op, list_to_str(self.args))
        return format_str.format(this_str)

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = "{}, {}".format(repr(self.op), list_to_repr(self.args))
        return format_repr.format(this_repr)


# +---------------------------------------------------------------------------+
# | If                                                                        |
# +---------------------------------------------------------------------------+
class If(Expr):
    def __init__(self, cond, true, false):
        super().__init__()
        self.cond = cond
        self.true = true
        self.false = false

    def __str__(self):
        format_str = super().__str__()
        this_str = "(if {} {} {})".format(self.cond, self.true, self.false)
        return format_str.format(this_str)

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = "{}, {}, {}".format(repr(self.cond),
                                        repr(self.true),
                                        repr(self.false))
        return format_repr.format(this_repr)


# +---------------------------------------------------------------------------+
# | Let                                                                       |
# +---------------------------------------------------------------------------+
class Let(Expr):
    def __init__(self, bindings, body):
        super().__init__()
        self.bindings = bindings
        self.body = body

    def __str__(self):
        format_str = super().__str__()
        this_str = "(let ({}) {})".format(list_to_str(self.bindings),
                                          self.body)
        return format_str.format(this_str)

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = "[{}], {}".format(list_to_repr(self.bindings),
                                      repr(self.body))
        return format_repr.format(this_repr)


class LetStar(Let):
    def __str__(self):
        format_str = super().__str__()
        this_str = "(let* ({}) {})".format(list_to_str(self.bindings),
                                           self.body)
        return format_str.format(this_str)


# +---------------------------------------------------------------------------+
# | While                                                                     |
# +---------------------------------------------------------------------------+
class While(Expr):
    def __init__(self, cond, while_bindings, body):
        super().__init__()
        self.cond = cond
        self.while_bindings = while_bindings
        self.body = body

    def __str__(self):
        format_str = super().__str__()
        bindings_str = list_to_str(self.while_bindings)
        this_str = "(while {} ({}) {})".format(self.cond,
                                               bindings_str,
                                               self.body)
        return format_str.format(this_str)

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = "{}, [{}], {}".format(repr(self.cond),
                                          list_to_repr(self.while_bindings),
                                          repr(self.body))
        return format_repr.format(this_repr)


class WhileStar(While):
    def __str__(self):
        format_str = super().__str__()
        bindings_str = list_to_str(self.while_bindings)
        this_str = "(while* {} ({}) {})".format(self.cond,
                                                bindings_str,
                                                self.body)
        return format_str.format(this_str)


# +---------------------------------------------------------------------------+
# | Cast                                                                      |
# +---------------------------------------------------------------------------+
class Cast(Expr):
    def __init__(self, body):
        super().__init__()
        self.body = body

    def __str__(self):
        format_str = super().__str__()
        this_str = "(cast {})".format(self.body)
        return format_str.format(this_str)

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = "{}".format(repr(self.body))
        return format_repr.format(this_repr)


# +---------------------------------------------------------------------------+
# | Pair                                                                      |
# +---------------------------------------------------------------------------+
class Pair(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = list_to_repr((self.name, self.value))
        return format_repr.format(this_repr)


class Property(Pair):
    def __str__(self):
        value_str = str(self.value)
        if type(self.value) in {tuple, list}:
            value_str = "({})".format(list_to_str(self.value))
        return ":{} {}".format(self.name, value_str)


class Binding(Pair):
    def __str__(self):
        return "[{} {}]".format(self.name, self.value)


# +---------------------------------------------------------------------------+
# | WhileBinding                                                              |
# +---------------------------------------------------------------------------+
class WhileBinding(ASTNode):
    def __init__(self, name, init, step):
        self.name = name
        self.init = init
        self.step = step

    def __str__(self):
        return "[{} {} {}]".format(self.name, self.init, self.step)

    def __repr__(self):
        format_repr = super().__repr__()
        this_repr = list_to_repr((self.name, self.init, self.step))
        return format_repr.format(this_repr)


# +---------------------------------------------------------------------------+
# | FPCore                                                                    |
# +---------------------------------------------------------------------------+
class FPCore(ASTNode):
    def __init__(self, arguments, properties, expression):
        self.arguments = arguments
        self.properties = properties
        self.expression = expression

    def __str__(self):
        arguments_str = list_to_str(self.arguments)
        properties_str = list_to_str(self.properties, "\n  ")
        return ("(FPCore ({})\n"
                "  {}\n"
                "  {})").format(arguments_str,
                                properties_str,
                                self.expression)

    def __repr__(self):
        arguments_repr = list_to_repr(self.arguments)
        properties_repr = list_to_repr(self.properties)
        return ("FPCore([{}],\n"
                "       [{}],\n"
                "       {})").format(arguments_repr,
                                     properties_repr,
                                     repr(self.expression))
