#! /usr/bin/env python3

import collections # OrderedDict
import sys         # exit

from pass_utils import UNOPS, BINOPS, ASSOC
from expression_walker import walk

def lift_inputs_and_assigns(exp):
  """ Extracts input variables and assignments from an expression """

  # Constants
  ATOMS     = {"Float", "Integer", "Input", "Variable"}
  ONE_ITEM  = UNOPS.union({"Return"})
  RECUR     = BINOPS.union(ONE_ITEM)

  # Function local variables
  assigns      = collections.OrderedDict() # name -> expression
  used_assigns = set()                     # assignments seen in the main exp
  inputs       = collections.OrderedDict() # name -> input range
  used_inputs  = set()                     # inputs seen in the main exp

  # A leading tuple must be an assign
  while type(exp[0]) is tuple:
    assignment = exp[0]
    assert(assignment[0] == "Assign")
    ganging = assignment[1]
    name = assignment[2]
    assert(name[0] == "Name")
    val  = assignment[3]
    # assign ganging is weaker than op ganging, only overide if no op ganging
    #   is present
    if ganging != None and val[1] == None:
      val = (val[0], ganging, *val[2:])
    # Explicit inputs
    assert(name[1] not in inputs)
    assert(name[1] not in assigns)
    if val[0] == "InputInterval":
      inputs[name[1]] = val
    # Assignment to an expression
    else:
      assigns[name[1]] = val

    # Work on the rest of the expression
    exp = exp[1]


  def _name(work_stack, count, exp):
    assert(exp[0] == "Name")
    assert(len(exp) == 2)

    if exp[1] in inputs:
      used_inputs.add(exp[1])
      assert(exp[1] not in assigns)
      work_stack.append((True, count, ("Input", exp[1])))
      return

    if exp[1] in assigns:
      used_assigns.add(exp[1])
      assert(exp[1] not in inputs)
      work_stack.append((True,  count, "Variable"))
      work_stack.append((True,  2,     exp[1]))
      work_stack.append((False, 2,     assigns[exp[1]]))
      return

    print("Use of undeclared name: {}".format(exp[1]))
    sys.exit(-1)

  my_expand_dict = {"Name": _name}
  new_exp = walk(my_expand_dict, dict(), exp, assigns)

  # Remove dead inputs
  dead_inputs = set(inputs).difference(used_inputs)
  for k in dead_inputs:
    del inputs[k]

  # Remove dead assigns
  dead_assigns = set(assigns).difference(used_assigns)
  for k in dead_assigns:
    del assigns[k]

  return new_exp, inputs, assigns








def runmain():
  from pass_utils import get_runmain_input
  from lexed_to_parsed import parse_function
  from pass_utils import print_exp, print_inputs, print_assigns

  data = get_runmain_input()
  exp  = parse_function(data)
  exp, inputs, assigns = lift_inputs_and_assigns(exp)

  print_inputs(inputs)
  print()
  print_assigns(assigns)
  print()
  print_exp(exp)


if __name__ == "__main__":
  try:
    runmain()
  except KeyboardInterrupt:
    print("\nGoodbye")
