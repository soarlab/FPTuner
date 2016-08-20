
import sys 

import tft_ir_api as IR 

var_AA = IR.RealVE("AA", 0, 0.0, 100.0)
var_BB = IR.RealVE("BB", 1, 0.0, 100.0)
var_CC = IR.RealVE("CC", 2, 0.0, 100.0)

rel = IR.BE("+", 4, IR.BE("+", 3, var_AA, var_BB), var_CC)

IR.TuneExpr(rel) 

# tft_ir_backend.ExportExpr2ExprsFile(rel, 0.01, "toy0.exprs")
# tft_ir_backend.ExportCppInsts(9, "toy0.cpp", "../__tft_alloc_text") 
