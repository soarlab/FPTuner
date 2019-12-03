
# ========
# sin(A/2) = +/- \sqrt{\frac{1 - cos(A)}{2.0}}
# ========

import math
import tft_ir_api as IR

x = IR.RealVE("x", 0, 0.0, 20.0)
a = IR.RealVE("a", 0, 1.0, 5.0)

x2   = IR.BE("*", 1, x, x)
a2   = IR.BE("*", 2, a, a)
a3   = IR.BE("*", 3, a, a2)

e_0  = IR.BE("*", 4, IR.FConst(-1.0), x2)
e_1  = IR.BE("*", 5, IR.FConst(2.0), a2)
e_2  = IR.BE("/", 6, e_0, e_1)
e    = IR.UE("exp", 7, e_2)

d_0  = IR.BE("*", 8, x2, e)
d    = IR.BE("/", 9, d_0, a3)

rel  = IR.BE("*", 10,
             IR.FConst(math.sqrt(2.0 / math.pi)),
             d)

IR.SetGroupWeight(7, 100.0)

IR.TuneExpr(rel)
