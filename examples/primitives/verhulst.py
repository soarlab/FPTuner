
import tft_ir_api as IR

const_r = IR.FConst(4.0)
const_k = IR.FConst(1.11)

var_x = IR.RealVE("x", 0, (0.1 - 1e-06), (0.3 + 1e-06)) 

temp0 = IR.BE("*", 1, const_r, var_x)

temp1 = IR.BE("/", 2, var_x, const_k)

temp2 = IR.BE("+", 3, IR.FConst(1.0), temp1)

rel = IR.BE("/", 4, temp0, temp2) 

IR.TuneExpr(rel) 
