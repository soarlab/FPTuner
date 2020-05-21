

from fpcore_ast import Variable, Number, Operation
from fpcore_logging import Logger
from gurobipy import GRB

import all_modifications_ast
import gurobipy as gp
import infix_str_ast


logger = Logger(level=Logger.HIGH, color=Logger.magenta)


class GurobiResult:
    BIT_WIDTH_ORDER = ["fp32", "fp64", "fp128"]
    DENOM_ORDER = [2**24, 2**53, 2**113]
    BIT_WIDTH_TO_DENOM = dict(zip(BIT_WIDTH_ORDER, DENOM_ORDER))

    def __init__(self, ssa, max_error, scale=1e3):
        self.max_error = max_error
        self.string_list = list()
        self.scale = scale
        self.ssa = ssa
        self.model = gp.Model()
        self.model.Params.OutputFlag = 0
        self.model.Params.NumericFocus = 3
        self.bit_width_bools = self.get_bit_width_bools()
        self.epses = self.get_epses()
        self.operation_bools = self.get_operation_bools()
        self.gurobi_defs = self.add_all_definitions()
        self.error = self.add_error()
        self.bit_width_costs = self.get_bit_width_costs()
        self.operation_costs = self.get_operation_costs()
        self.cost = self.add_cost()

        self.model.addConstr(self.error <= scale*max_error)
        self.model.update()
        self.string_list.append("{} <= {}*{}".format(self.error.VarName, scale, max_error))

        self.model.setObjective(self.cost, GRB.MINIMIZE)
        self.string_list.append("minimize {}".format(self.cost.VarName))

        logger.log("gurobi query:\n{}\n", "\n".join(self.string_list))

        self.model.optimize()

    def get_bit_width_bools(self):
        bit_width_bools = dict()
        for name in self.ssa.fptaylor_forms:
            bools = dict()
            for bit_width in self.ssa.search_space["bit_widths"]:
                new_name = "{}_is_{}".format(name, bit_width)
                new_var = self.model.addVar(vtype=GRB.BINARY, name=new_name)
                self.string_list.append("bool {}".format(new_name))
                bools[bit_width] = new_var
            self.model.addConstr(sum(bools.values()) == 1)
            self.model.update()
            self.string_list.append("1 = {}".format(" + ".join([v.VarName for v in bools.values()])))
            bit_width_bools[name] = bools
        return bit_width_bools

    def get_epses(self):
        epses = dict()
        for name, bools in self.bit_width_bools.items():
            parts = list()
            str_parts = list()
            for bit_width in self.ssa.search_space["bit_widths"]:
                denom = GurobiResult.BIT_WIDTH_TO_DENOM[bit_width]
                var = bools[bit_width]
                parts.append(var*self.scale / denom)
                str_parts.append("{}*{}/{}".format(var.VarName, self.scale, denom))
            final_eps = self.model.addVar(name="{}_eps".format(name))
            self.model.addConstr(final_eps == sum(parts))
            self.model.update()
            self.string_list.append("real {} = {}".format(final_eps.VarName,
                                                          " + ".join(str_parts)))
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
                self.string_list.append("bool {}".format(new_name))
            self.model.addConstr(sum(bools.values()) == 1)
            self.model.update()
            self.string_list.append("1 = {}".format(" + ".join([v.VarName for v in bools.values()])))
            operation_bools[name] = bools
        return operation_bools

    def add_all_definitions(self):
        gurobi_defs = dict()
        for name, forms in self.ssa.fptaylor_forms.items():
            eps = self.epses[name]
            new_var = self.model.addVar(name="{}_error".format(name))
            if name not in self.operation_bools:
                default = forms["default"]
                val, val_str = default.to_gurobi(eps, self.scale)
                self.model.addConstr(new_var == val)
                gurobi_defs[name] = new_var
                self.model.update()
                self.string_list.append("{} = {}".format(new_var.VarName, val_str))
                continue
            options = list()
            options_str = list()
            for tup, form in forms.items():
                if type(tup) == str and tup == "default":
                    oper = self.ssa.definitions[name].op
                    bool = self.operation_bools[name][oper]
                    val, val_str = forms["default"].to_gurobi(eps, self.scale)
                    options.append(val * bool)
                    options_str.append("({})*{}".format(val_str, bool.VarName))
                    continue
                target_name, oper = tup
                bool = self.operation_bools[target_name][oper]
                val, val_str = form.to_gurobi(eps, self.scale)
                options.append(val * bool)
                options_str.append("({})*{}".format(val_str, bool.VarName))
            self.model.addConstr(new_var == sum(options))
            self.model.update()
            self.string_list.append("{} = {}".format(new_var.VarName, " + ".join(options_str)))
            gurobi_defs[name] = new_var
        return gurobi_defs

    def add_error(self):
        error = self.model.addVar(name="total_error")
        self.model.addConstr(error == sum(self.gurobi_defs.values()))
        self.model.update()
        self.string_list.append("{} = {}".format(error.VarName,
                                                 " + ".join([v.VarName for v in self.gurobi_defs.values()])))
        return error

    def get_bit_width_costs(self):
        costs = dict()
        for name, bools in self.bit_width_bools.items():
            cost = self.model.addVar(name="{}_bit_width_cost".format(name))
            cost_pairs = list(zip(range(1, len(bools)+1), bools.values()))
            self.model.addConstr(cost == sum([i*b for i, b in cost_pairs]))
            costs[name] = cost
            self.model.update()
            self.string_list.append("{} = {}".format(cost.VarName,
                                                     " + ".join(["{}*{}".format(i, b.VarName) for i,b in cost_pairs])))
        return costs

    def get_operation_costs(self):
        costs = dict()
        for name, bools in self.operation_bools.items():
            op = self.ssa.definitions[name].op
            op_costs = [all_modifications_ast.OperationToCost[oper]
                        for oper in self.ssa.search_space["operations"][op]]
            cost_pairs = list(zip(op_costs, bools.values()))
            cost = self.model.addVar(name="{}_operation_cost".format(name))
            self.model.addConstr(cost == sum([c*b for c, b in cost_pairs]))
            self.model.update()
            costs[name] = cost
            self.string_list.append("{} = {}".format(cost.VarName,
                                                     " + ".join(["{}*{}".format(c, b.VarName) for c,b in cost_pairs])))
        return costs

    def add_cost(self):
        cost = self.model.addVar(name="total_cost")
        self.model.addConstr(cost == sum(self.bit_width_costs.values())
                             + sum(self.operation_costs.values()))
        self.model.update()
        self.string_list.append("{} = {} + {}".format(cost.VarName,
                                                      " + ".join([v.VarName for v in self.bit_width_costs.values()]),
                                                      " + ".join([v.VarName for v in self.operation_costs.values()])))
        return cost

