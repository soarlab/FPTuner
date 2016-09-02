
import tft_ir_api as IR 

var_u = IR.RealVE("u", 0, (-30.0 - 0.0001), (120.0 + 0.0001)) 
var_v = IR.RealVE("v", 1, (320.0 - 0.00001), (20300.0 + 0.00001)) 
var_T = IR.RealVE("T", 2, (-50.0 - 0.000000001), (30.0 + 0.000000001)) 

t1   = IR.BE("+",  4, IR.FConst(331.4), IR.BE("*",  3, IR.FConst(0.6), var_T)) 

temp = IR.BE("+",  5, t1, var_u)
temp = IR.BE("*",  8, temp, temp) 

r    = IR.BE("/",  9, IR.BE("*",  7, IR.UE("-",  6, t1), var_v), temp) 

IR.TuneExpr(r) 
