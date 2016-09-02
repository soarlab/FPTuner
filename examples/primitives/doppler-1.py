
import tft_ir_api as IR 

var_u = IR.RealVE("u", 0, (-100.0 - 0.0000001), (100.0 + 0.0000001)) 
var_v = IR.RealVE("v", 1, (20.0 - 0.000000001), (20000.0 + 0.000000001)) 
var_T = IR.RealVE("T", 2, (-30.0 - 0.000001), (50.0 + 0.000001)) 

t1   = IR.BE("+",  4, IR.FConst(331.4), IR.BE("*",  3, IR.FConst(0.6), var_T)) 

temp = IR.BE("+",  5, t1, var_u)
temp = IR.BE("*",  8, temp, temp) 

r    = IR.BE("/",  9, IR.BE("*",  7, IR.UE("-",  6, t1), var_v), temp) 

IR.TuneExpr(r) 
