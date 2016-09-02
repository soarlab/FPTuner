
import tft_ir_api as IR

const_r = IR.FConst(4.0) 
const_k = IR.FConst(1.11) 

var_x = IR.RealVE("x", 0, 0.1, 0.3) 

temp0 = IR.BE("*", 2, IR.BE("*", 1, const_r, var_x), var_x)
temp1 = IR.BE("/", 3, var_x, const_k)
temp2 = IR.BE("+", 4, temp1, temp1)
temp3 = IR.BE("+", 5, IR.FConst(1.0), temp2)

rel = IR.BE("/", 6, temp0, temp3) 

IR.TuneExpr(rel) 
