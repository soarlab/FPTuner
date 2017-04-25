
import tft_ir_api as IR 

gid = 0

x = IR.RealVE("x", gid, 0.01, 100.0)
gid += 1

y = IR.RealVE("y", gid, 0.01, 100.0)
gid += 1

x2 = IR.BE("*", gid, x, x)
gid += 1

y2 = IR.BE("*", gid, y, y)
gid += 1

x2y2 = IR.BE("+", gid, x2, y2)
gid += 1

sqrt_x2y2 = IR.UE("sqrt", gid, x2y2)
gid += 1

sqrt_x = IR.BE("+", gid, sqrt_x2y2, x)
gid += 1

two_sqrt_x = IR.BE("*", gid, IR.FConst(2.0), sqrt_x)
gid += 1

sqrt_all = IR.UE("sqrt", gid, two_sqrt_x)
gid += 1

half_sqrt_all = IR.BE("*", gid, IR.FConst(0.5), sqrt_all)

IR.TuneExpr(half_sqrt_all)

