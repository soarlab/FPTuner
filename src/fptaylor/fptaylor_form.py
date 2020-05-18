

from fpcore_ast import Operation
from fpcore_logging import Logger
from fptaylor_lexer import FPTaylorLexer
from fptaylor_parser import FPTaylorParser
from gelpia_result import GelpiaResult


logger = Logger(level=Logger.HIGH, color=Logger.cyan)


class FPTaylorForm:
    # Get the expression parser ready
    LEXER = FPTaylorLexer()
    PARSER = FPTaylorParser()

    def __init__(self, exp, form):
        if exp is None and form is None:
            return
        exp = int(exp)
        if type(form) == str:
            tokens = FPTaylorForm.LEXER.tokenize(form)
            expr = FPTaylorForm.PARSER.parse(tokens)
            form = expr
        self.forms = {exp: form}
        self.maximums = {exp: None}

    def __str__(self):
        parts = list()
        for exp, form in self.forms.items():
            maximum = self.maximums[exp] or "not_calculated"
            part = "(exp={} form={} max={})".format(exp, form, maximum)
            parts.append(part)
        return " + ".join(parts)

    def __eq__(self, other):
        if len(self.forms) != other.forms:
            return False
        for exp in self.forms:
            if exp not in other.forms or self.forms[exp] != other.forms[exp]:
                return False
        return True

    def __add__(self, other):
        retval = FPTaylorForm(None, None)
        retval.forms = dict()
        for exp, form in self.forms.items():
            retval.forms[exp] = form
        for exp, form in other.forms.items():
            if exp in retval.forms:
                old = retval.forms[exp]
                retval.forms[exp] = Operation("+", old, form)
            else:
                retval.forms[exp] = form
        retval.maximums = {exp: None for exp in retval.forms}
        return retval

    def change_exp(self, old_exp, new_exp):
        if old_exp not in self.forms:
            return
        old_form = self.forms[old_exp]
        if new_exp in self.forms:
            existing = self.forms[new_exp]
            self.forms[new_exp] = Operation("+", existing, old_form)
        else:
            self.forms[new_exp] = old_form
        self.maximums[new_exp] = None

        del self.forms[old_exp]
        del self.maximums[old_exp]

    def expand_forms(self, ssa):
        new_forms = dict()
        for exp, form in self.forms.items():
            new_forms[exp] = form.expand(ssa)
        self.forms = new_forms

    def maximize(self, inputs, memoized):
        for exp, form in self.forms.items():
            key = str(inputs) + str(form)
            if key not in memoized:
                memoized[key] = GelpiaResult(inputs, form).max_upper
            else:
                logger("Memoized result for: {}", key)
            self.maximums[exp] = memoized[key]

    def to_gurobi(self, eps, scale):
        parts = list()
        parts_str = list()
        for exp, maximum in self.maximums.items():
            if exp == "eps":
                parts.append(eps*maximum*scale)
                parts_str.append("{}*{}*{}".format(eps.VarName, maximum, scale))
            else:
                parts.append((2**exp)*maximum*scale)
                parts_str.append("{}*{}*{}".format(2**exp, maximum, scale))
        return sum(parts), " + ".join(parts_str)
