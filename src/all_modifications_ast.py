

from collections import OrderedDict
from fpcore_lexer import FPCoreLexer

import can_have_fptaylor_form_ast
import equals_ast
import expand_ast
import fpcore_ast
import infix_str_ast
import to_single_assignment_ast

OperationTable = [
    #originalOp,   operation       FPTaylorOperation                  Cost
    ("sin",        "zero_sin",     "zero_sin",                        0),
    ("sin",        "one_sin",      "one_sin",                         0),
    ("sin",        "m_one_sin",    "m_one_sin",                       0),
    ("sin",        "taylor_1_sin", "taylor_1_sin",                    1),
    ("sin",        "taylor_3_sin", "taylor_3_sin",                    2),
    ("sin",        "mlm_1024_sin", "rnd[64,ne,1024.50,-53,-1022](sin", 3),
    ("sin",        "mlm_128_sin",  "rnd[64,ne,128.50,-53,-1022](sin",  4),
    ("sin",        "mlm_8_sin",    "rnd[64,ne,8.50,-53,-1022](sin",    5),
    ("sin",        "mlm_4_sin",    "rnd[64,ne,4.50,-53,-1022](sin",    6),
    ("sin",        "sin",          "sin",                             10),
    ("exp",        "mlm_1024_exp", "rnd[64,ne,1024.50,-53,-1022](exp", 3),
    ("exp",        "mlm_128_exp",  "rnd[64,ne,128.50,-53,-1022](exp",  4),
    ("exp",        "mlm_8_exp",    "rnd[64,ne,8.50,-53,-1022](exp",    5),
    ("exp",        "mlm_4_exp",    "rnd[64,ne,4.50,-53,-1022](exp",    6),
    #("exp",        "mlm_1_exp",    "rnd[64,ne,1.50,-53,-1022](exp",    7),
    ("exp",        "exp",          "exp",                             10),
    ("log",        "mlm_1024_log", "rnd[64,ne,1024.50,-53,-1022](log", 3),
    ("log",        "mlm_128_log",  "rnd[64,ne,128.50,-53,-1022](log",  4),
    ("log",        "mlm_8_log",    "rnd[64,ne,8.50,-53,-1022](log",    5),
    ("log",        "mlm_4_log",    "rnd[64,ne,4.50,-53,-1022](log",    6),
    #("log",        "mlm_1_log",    "rnd[64,ne,1.50,-53,-1022](log",    7),
    ("log",        "log",          "log",                             10),

]

OperationToFPTaylor = dict([(row[1],row[2]) for row in OperationTable])
FPTaylorToOperation = dict([(row[2],row[1]) for row in OperationTable])
OperationToCost = dict([(row[1],row[3]) for row in OperationTable])
for row in OperationTable:
    FPCoreLexer.UNARY_OPERATIONS.add(row[1])
