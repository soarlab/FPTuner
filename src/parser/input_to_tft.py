#!/usr/bin/env python3

from pass_utils import *

import collections
import sys



def to_python(exp, inputs, assigns, weights, precs):

  def _to_python(exp):
    tag = exp[0]

    if tag in {"Integer", "Float"}:
      return  ['IR.FConst('] + [exp[1]] + [')']

    if tag in INFIX or tag in BINOPS:
      return (['IR.BE("{}",'.format(tag)]
              + [str(exp[1])] + [',']
              + _to_python(exp[2]) + [',']
              + _to_python(exp[3]) + [')'])

    if tag == "neg":
      return (['IR.UE("-",']
              + [str(exp[1])] + [',']
              + _to_python(exp[2]) + [')'])

    if tag in UNOPS:
      return (['IR.UE("{}",'.format(tag)]
              + [str(exp[1])] + [',']
              + _to_python(exp[2]) + [')'])

    if tag in {"Input", "Variable"}:
      return [exp[1]]

    if tag in {"Return"}:
      return ['IR.TuneExpr('] + _to_python(exp[1]) + [')']


    print("to_python error unknown: '{}'".format(exp))
    sys.exit(-1)

  function = ["import tft_ir_api as IR\n"]
  function += ['{} = IR.RealVE("{}",{},{},{})\n'.format(n, n, v[1], v[2][1], v[3][1])
              for n,v in inputs.items()]
  function += ["{} = {}\n".format(n, ''.join(_to_python(v))) for n,v in assigns.items()]
  function += ['IR.SetGroupWeight({}, {}.0)\n'.format(g,w) for g,w in weights.items()]
  function +=  _to_python(exp)

  return ''.join(function)



def translate(data):
  from lexed_to_parsed import parse_function
  from pass_lift_inputs_and_assigns import lift_inputs_and_assigns
  from pass_set_gangs import set_gangs
  exp = parse_function(data)
  exp, inputs, assigns = lift_inputs_and_assigns(exp)
  exp, inputs, assigns, weights, precs = set_gangs(exp, inputs, assigns)

  return to_python(exp, inputs, assigns, weights, precs)


def runmain():
  from lexed_to_parsed import parse_function
  from pass_lift_inputs_and_assigns import lift_inputs_and_assigns

  data = get_runmain_input()
  py_src = translate(data)

  print(py_src)


if __name__ == "__main__":
  try:
    runmain()
  except KeyboardInterrupt:
    print("\nGoodbye")
