

from ast_modifier import add_method
from exceptions import (BadPreError, ClassError, DomainError, FeatureError,
                        NoPreError, OperationError, UnsupportedError,
                        VariableError)
from fpcore_ast import (ASTNode, Binding, Cast, Constant, FPCore, If, Let,
                        LetStar, Number, Operation, Variable, While, WhileStar)
from fpcore_logging import Logger
from single_assignment import SingleAssignment


logger = Logger()


SUPPORTED = {"*", "+", "-", "/", "atan", "cos", "exp", "log", "pow", "sin",
             "sqrt", "tan"}


@add_method(ASTNode)
def to_single_assignment(self, ssa, environment_stack):
    raise ClassError("to_single_assignment", type(self).__name__)


# Only override func for leaf classes so unimplemented versions are caught by
# ASTNode. We still want to check all Expr subclasses for properties, but
# we will have to do that manually.
def check_properties(self, ssa, environment_stack):
    if len(self.properties) != 0:
        logger.warning("Dropping properties '{}' in expression '{}'",
                       self.properties, self)


@add_method(Constant)
def to_single_assignment(self, ssa, environment_stack):
    # todo: handle Constants and match FPTaylor constants
    raise FeatureError("FPCore constants")


@add_method(Variable)
def to_single_assignment(self, ssa, environment_stack):
    check_properties(self, ssa, environment_stack)

    # First search the environment stack
    for environment in reversed(environment_stack):
        # If found transform the value
        # Note: all environment bodies should be expanded
        if self.source in environment:
            body = environment[self.source]
            return body.to_single_assignment(ssa, environment_stack)

    # Then check for an input
    if self.source in ssa.inputs:
        new_name = ssa.add_subexpression(self)
        return Variable(new_name)

    # Exit if no definition is found
    raise VariableError(self.source)


@add_method(Number)
def to_single_assignment(self, ssa, environment_stack):
    check_properties(self, ssa, environment_stack)

    # Add it to the ssa
    new_name = ssa.add_subexpression(self)
    return Variable(new_name)


@add_method(Operation)
def to_single_assignment(self, ssa, environment_stack):
    check_properties(self, ssa, environment_stack)

    # Check if we support the operation
    # The FPCore parser supports more operations than FPTuner does
    if self.op not in SUPPORTED:
        # todo: flesh out supported operations
        raise OperationError(self.op)

    # Transform all arguments and add a new operation
    args = [a.to_single_assignment(ssa, environment_stack)
            for a in self.args]
    new_name = ssa.add_subexpression(Operation(self.op, *args))
    return Variable(new_name)


@add_method(If)
def to_single_assignment(self, ssa, environment_stack):
    raise UnsupportedError("if")


@add_method(Let)
def to_single_assignment(self, ssa, environment_stack):
    check_properties(self, ssa, environment_stack)

    # Setup the new entry in the environment stack
    binding_list = [b.to_single_assignment(ssa, environment_stack)
                    for b in self.bindings]
    new_environment = dict(binding_list)
    environment_stack.append(new_environment)

    # Transform body using the updated stack
    return self.body.to_single_assignment(ssa, environment_stack)


@add_method(LetStar)
def to_single_assignment(self, ssa, environment_stack):
    check_properties(self, ssa, environment_stack)

    # Bindings may reference previous bindings in the let
    # So add each to the stack one at a time
    for b in self.bindings:
        name, val = b.to_single_assignment(ssa, environment_stack)
        environment_stack.append({name: val})

    # Transform body using the updated stack
    return self.body.to_single_assignment(ssa, environment_stack)


@add_method(While)
def to_single_assignment(self, ssa, environment_stack):
    raise UnsupportedError("while")


@add_method(WhileStar)
def to_single_assignment(self, ssa, environment_stack):
    raise UnsupportedError("while*")


@add_method(Cast)
def to_single_assignment(self, ssa, environment_stack):
    raise UnsupportedError("cast")


@add_method(Binding)
def to_single_assignment(self, ssa, environment_stack):
    # Expand body using the environment stack
    # This should allow shadowing
    expanded = self.value.expand(ssa, environment_stack)

    # Note: This deviates from the normal return of a Variable. An environment
    # mapping pair is returned.
    return self.name.source, expanded


def properties_to_argument_domains(fpcore):
    # Take an FPCore and return and argument->domain mapping
    # An incomplete mapping is an error
    arguments = fpcore.arguments
    properties = fpcore.properties

    def normalize_comparison(comp):
        # given an n-arry comparison return a list of comparisons which all use
        # "<=" and only have two arguments

        # Only simple domains are supported
        # todo: add support for constant mathematical domains (eg (- 1 1/256))
        if any([type(a) not in {Variable, Number} for a in comp.args]):
            logger.warning("Dropping precondition: {}", comp)
            return list()

        # Make exclusive comparisons inclusive
        if comp.op in {"<", ">"}:
            logger.warning("Turning exclusive bound to inclusive: {}", comp)
            comp.op += "="

        # Normalize => to >=
        if comp.op == "=>":
            comp.op = ">="

        # Reverse if comparison was >=
        if comp.op == ">=":
            comp.op = "<="
            comp.args = list(reversed(comp.args))

        # Break comparison into overlaping pairs
        ret_list = list()
        for i in range(len(comp.args)-1):
            ret_list.append(Operation("<=", comp.args[i], comp.args[i+1]))
        return ret_list

    def get_domains(precondition_list):
        lower_domains = {a.source: None for a in arguments}
        upper_domains = {a.source: None for a in arguments}

        def is_input(x):
            return type(x) == Variable and x.source in upper_domains

        for pre in precondition_list:

            # We only get domains from comparisons
            if pre.op not in {"<", ">", "<=", ">=", "=>"}:
                logger.warning("Dropping precondition: {}", pre)
                continue

            # Get list of pairs
            normal = normalize_comparison(pre)
            for comp in normal:

                # If the comparison is (<= <Variable> <Number>) it is an upper
                # bound
                if is_input(comp.args[0]) and type(comp.args[1]) == Number:
                    upper_domains[str(comp.args[0])] = comp.args[1]
                    continue

                # If the comparison is (<= <Number> <Variable>) it is a lower
                # bound
                if type(comp.args[0]) == Number and is_input(comp.args[1]):
                    lower_domains[str(comp.args[1])] = comp.args[0]
                    continue

                # Only simple domains are supported
                logger.warning("Dropping precondition: {}", comp)

        # Bring upper and lower bounds together
        domains = dict()
        for name in lower_domains:
            domains[name] = (lower_domains[name], upper_domains[name])
        return domains

    # Search the FPCore's properties for the :pre property
    # todo: add support for multiple ':pre' properties
    pre = None
    for prop in properties:
        if prop.name == "pre":
            pre = prop
            continue

    # If we couldn't find ':pre' there is no domain
    if pre is None:
        raise NoPreError()

    # If pre is not an Operation we can't handle it
    if type(pre.value) != Operation:
        raise BadPreError(pre)

    # The pre can be a single bound description, or multiple joined with an and
    if pre.value.op == "and":
        property_list = list(pre.value.args)
    else:
        property_list = [pre.value]

    # Get domains and check that all are there
    domains = get_domains(property_list)
    for var, val in domains.items():
        if val[0] is None or val[1] is None:
            raise DomainError(val[0], val[1], var)

    return domains


@add_method(FPCore)
def to_single_assignment(self, search_space):
    # Note: This deviates from the other functions by taking a search space and
    #       Returning a SingleAssignment
    ssa = SingleAssignment(search_space)

    # Get the name
    name = "func"
    for prop in self.properties:
        if prop.name == "name":
            name = prop.value

    # Grab domain bounds
    domains = properties_to_argument_domains(self)
    initial_environment = dict()
    for name, domain in domains.items():
        # If the domain contains a single point we treat that as a literal
        # in the environment
        if domain[0] == domain[1]:
            initial_environment[name] = domain[0]
            continue
        ssa.add_input(str(name), domain)

    # Transform the main expression
    self.expression.to_single_assignment(ssa, [initial_environment])
    return ssa
