
import tft_ir_api as IR

gid = 0

a = IR.RealVE('a', gid  , -1.0, 1.0)
b = IR.RealVE('b', gid+1, -1.0, 1.0)
gid += 2

rel = IR.BE('/', gid+2,
            IR.BE('+', gid, a, b),
            IR.BE('*', gid+1, a, b))
gid += 3

IR.TuneExpr(rel)
