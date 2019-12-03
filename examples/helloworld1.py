
import sys

import tft_ir_api as IR

var_AA = IR.RealVE("AA", 0, 0.0, 100.0)

rel = IR.BE("+", 2, IR.BE("+", 1, var_AA, IR.FConst(99.99)), IR.FConst(99.99))

IR.TuneExpr(rel)
