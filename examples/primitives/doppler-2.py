
import tft_ir_api as IR

var_u = IR.RealVE("u", 0, (-125.0 - 0.000000000001), (125.0 + 0.000000000001))
var_v = IR.RealVE("v", 1, (15.0 - 0.001), (25000.0 + 0.001))
var_T = IR.RealVE("T", 2, (-40.0 - 0.00001), (60.0 + 0.00001))

t1   = IR.BE("+",  4, IR.FConst(331.4), IR.BE("*",  3, IR.FConst(0.6), var_T))

temp = IR.BE("+",  5, t1, var_u)
temp = IR.BE("*",  8, temp, temp)

r    = IR.BE("/",  9, IR.BE("*",  7, IR.UE("-",  6, t1), var_v), temp)

IR.TuneExpr(r)
