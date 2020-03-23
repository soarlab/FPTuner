

from fpcore_logging import Logger
from ast_modifier import add_method
from exceptions import ClassError, VariableError
from fpcore_ast import ASTNode, Atom, Variable, Operation


logger = Logger()


@add_method(ASTNode)
def expand(self, ssa, environment_stack=None):
    # Make sure calling expand leads to an error if not overridden
    class_name = type(self).__name__
    raise ClassError("expand", class_name)


@add_method(Atom)
def expand(self, ssa, environment_stack=None):
    # Atoms are left alone, except for variables which are handled below
    return self


@add_method(Variable)
def expand(self, ssa, environment_stack=None):
    # First search the environment stack
    if environment_stack is not None:
        for environment in reversed(environment_stack):
            # If found expand and return the value
            if self.source in environment:
                return environment[self.source].expand(ssa, environment_stack)

    # Then check definitions and inputs
    if self.source in ssa.definitions:
        return ssa.definitions[self.source].expand(ssa, environment_stack)
    if self.source in ssa.inputs:
        return self

    # Exit if no definition is found
    raise VariableError(self.source)


@add_method(Operation)
def expand(self, ssa, environment_stack=None):
    # Expand all arguments and return a new operation
    args = [a.expand(ssa, environment_stack) for a in self.args]
    return Operation(self.op, *args)
