#! /usr/bin/env python3

import sys

from pass_utils import UNOPS, BINOPS, ASSOC
from expression_walker import walk, no_mut_walk

def set_gangs(exp, inputs, assigns):
  # Find all used gangs
  used_gangs = set()
  for v in inputs.values():
    if v[1] != None and v[1][0] == "G":
      used_gangs.add(int(v[1][1:]))
  for v in assigns.values():
    if v[1] != None and v[1][0] == "G":
      used_gangs.add(int(v[1][1:]))

  def expand_two(work_stack, count, exp):
    assert(len(exp) == 4)
    if exp[1] != None and exp[1][0] == "G":
      used_gangs.add(int(exp[1][1:]))
    work_stack.append((False, 2, exp[3]))
    work_stack.append((False, 2, exp[2]))

  def expand_one(work_stack, count, exp):
    assert(len(exp) == 3)
    if exp[1] != None and exp[1][0] == "G":
      used_gangs.add(int(exp[1][1:]))
    work_stack.append((False, 1, exp[2]))

  my_expand_dict = dict()
  my_expand_dict.update(zip(BINOPS, [expand_two  for _ in BINOPS]))
  my_expand_dict.update(zip(UNOPS,  [expand_one  for _ in UNOPS]))

  no_mut_walk(my_expand_dict, exp, assigns)

  # Assign unused gang numbers to unassigned exps
  assert(len(used_gangs) == 0 or min(used_gangs) >= 0)
  if len(used_gangs) == 0:
    possible_gangs = {1}
  else:
    possible_gangs = set(range(min(used_gangs), max(used_gangs)+1))
    possible_gangs = possible_gangs.difference(used_gangs)

  def new_gang():
    if len(possible_gangs) == 0:
      g = max(used_gangs) + 1
    else:
      g = min(possible_gangs)
      possible_gangs.remove(g)
    used_gangs.add(g)
    return g

  # Lift out weights and precisions, and replace gang strings with integers
  weights = dict()
  precs = dict()
  def fix_gang(exp):
    ga = exp[1]
    if type(ga) is int:
      return exp
    elif ga == None:
      return (exp[0], new_gang(), *exp[2:])
    elif ga[0] == "G":
      return (exp[0], int(ga[1:]), *exp[2:])
    elif ga[0] == "W":
      g = new_gang()
      weights[g] = int(ga[1:])
      return (exp[0], g, *exp[2:])
    elif ga[0] == "P":
      g = new_gang()
      precs[g] = int(ga[1:])
      return (exp[0], g, *exp[2:])
    else:
      print(exp)
      assert(0)


  for k,v in inputs.items():
    inputs[k] = fix_gang(v)
  for k,v in assigns.items():
    assigns[k] = fix_gang(v)

  def expand_two(work_stack, count, exp):
    assert(len(exp) == 4)
    exp = fix_gang(exp)
    work_stack.append((True,  count, (exp[0], exp[1])))
    work_stack.append((False, 2,     exp[3]))
    work_stack.append((False, 2,     exp[2]))

  def expand_one(work_stack, count, exp):
    assert(len(exp) == 3)
    exp = fix_gang(exp)
    work_stack.append((True,  count, (exp[0], exp[1])))
    work_stack.append((False, 1,     exp[2]))

  my_expand_dict = dict()
  my_expand_dict.update(zip(BINOPS, [expand_two  for _ in BINOPS]))
  my_expand_dict.update(zip(UNOPS,  [expand_one  for _ in UNOPS]))

  new_exp = walk(my_expand_dict, dict(), exp, assigns)

  return new_exp, inputs, assigns, weights, precs
