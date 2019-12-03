
import math
import tft_ir_api as IR

r   = IR.RealVE("r", 0, 1.0, 10.0)
h   = IR.RealVE("h", 1, 1.0, 10.0)
pi  = IR.FConst(math.pi)

h2  = IR.BE("*", 2, h, h)
r2  = IR.BE("*", 3, r, r)
hr2 = IR.BE("+", 4, h2, r2)
pir = IR.BE("*", 5, pi, r)

tm1 = IR.UE("sqrt", 6, hr2)
tm2 = IR.BE("+",    7, r, tm1)
rel = IR.BE("*",    8, pir, tm2)

IR.SetGroupWeight(6, 16.0)

IR.TuneExpr(rel)
