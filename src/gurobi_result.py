

from fpcore_ast import Variable, Number, Operation
from fpcore_logging import Logger
from gurobipy import GRB

import gurobipy as gp
import infix_str_ast


logger = Logger(level=Logger.HIGH)


class GurobiResult:
    BIT_WIDTH_ORDER = ["fp32", "fp64", "fp128"]
    DENOM_ORDER = [2**24, 2**53, 2**113]
    BIT_WIDTH_TO_DENOM = dict(zip(BIT_WIDTH_ORDER, DENOM_ORDER))

    def __init__(self, ssa, scale=1000):
        self.scale = scale
        self.ssa = ssa
        self.model = gp.Model()
        self.model.Params.OutputFlag = 0
        self.eps_bools = self.get_eps_bools()
        self.epses = self.get_epses()
        self.operation_bools = self.get_operation_bools()
        self.gurobi_defs = self.add_all_definitions()
        self.error = self.add_error()
        self.bit_width_costs = self.get_bit_width_costs()
        self.operation_costs = self.get_operation_costs()
        self.cost = self.add_cost()

        max_error = self.ssa.search_space["error_bound"]
        self.model.addConstr(self.error <= scale*max_error)
        self.model.setObjective(self.cost, GRB.MINIMIZE)
        self.model.optimize()

    def get_eps_bools(self):
        eps_bools = dict()
        for name in self.ssa.fptaylor_forms:
            bools = dict()
            for bit_width in self.ssa.search_space["bit_widths"]:
                new_name = "{}_is_{}".format(name, bit_width)
                new_var = self.model.addVar(vtype=GRB.BINARY, name=new_name)
                bools[bit_width] = new_var
            self.model.addConstr(sum(bools.values()) == 1)
            eps_bools[name] = bools
        return eps_bools

    def get_epses(self):
        epses = dict()
        for name, bools in self.eps_bools.items():
            parts = list()
            for bit_width in self.ssa.search_space["bit_widths"]:
                denom = GurobiResult.BIT_WIDTH_TO_DENOM[bit_width]
                var = bools[bit_width]
                parts.append(var*self.scale / denom)
            final_eps = self.model.addVar()
            self.model.addConstr(final_eps == sum(parts))
            epses[name] = final_eps
        return epses

    def get_operation_bools(self):
        operation_bools = dict()
        for name in self.ssa.operations:
            bools = dict()
            op = self.ssa.definitions[name].op
            for oper in self.ssa.search_space["operations"][op]:
                new_name = "{}_is_{}".format(name, oper)
                new_var = self.model.addVar(vtype=GRB.BINARY, name=new_name)
                bools[oper] = new_var
            self.model.addConstr(sum(bools.values()) == 1)
            operation_bools[name] = bools
        return operation_bools

    def add_all_definitions(self):
        gurobi_defs = dict()
        for name, forms in self.ssa.fptaylor_forms.items():
            eps = self.epses[name]
            new_var = self.model.addVar()
            if name not in self.operation_bools:
                default = forms["default"]
                self.model.addConstr(new_var == default.to_gurobi(eps))
                gurobi_defs[name] = new_var
                continue
            options = list()
            for tup, form in forms.items():
                if type(tup) == str and tup == "default":
                    oper = self.ssa.definitions[name].op
                    bool = self.operation_bools[name][oper]
                    options.append(forms["default"].to_gurobi(eps) * bool)
                    continue
                target_name, oper = tup
                bool = self.operation_bools[target_name][oper]
                options.append(form.to_gurobi(eps) * bool)
            self.model.addConstr(new_var == sum(options))
            gurobi_defs[name] = new_var
        return gurobi_defs

    def add_error(self):
        error = self.model.addVar()
        self.model.addConstr(error == sum(self.gurobi_defs.values()))
        return error

    def get_bit_width_costs(self):
        costs = dict()
        for name, bools in self.eps_bools.items():
            cost = sum([i*b for i, b in
                        zip(range(len(bools)), bools.values())])
            costs[name] = cost
        return costs

    def get_operation_costs(self):
        costs = dict()
        for name, bools in self.operation_bools.items():
            cost = sum([i*b for i, b in
                        zip(range(len(bools)), bools.values())])
            costs[name] = cost
        return costs

    def add_cost(self):
        cost = self.model.addVar()
        self.model.addConstr(cost == sum(self.bit_width_costs.values())
                             + sum(self.operation_costs.values()))
        return cost

