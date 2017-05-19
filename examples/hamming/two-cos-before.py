
import tft_ir_api as IR

gid = 0
x = IR.RealVE('x', gid  , -10.0, 10.0)
e = IR.RealVE('e', gid+1, -0.000001, 0.000001)
gid += 2

temp0 = IR.BE('+', gid, x, e)
temp1 = IR.UE('cos', gid+1, temp0)

rel = IR.BE('-', gid+3,
            temp1,
            IR.UE('cos', gid+2, x))

IR.TuneExpr(rel) 
