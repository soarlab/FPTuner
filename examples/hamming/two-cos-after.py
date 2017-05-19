
import tft_ir_api as IR

gid = 0
x = IR.RealVE('x', gid  , -10.0, 10.0)
e = IR.RealVE('e', gid+1, -0.000001, 0.000001)
gid += 2

temp0 = IR.UE('sin', gid+1, IR.BE('/', gid, e, IR.FConst(2.0)))
gid += 2

temp1 = IR.BE('/', gid+2,
              IR.BE('+', gid+1, x, IR.BE('+', gid, x, e)),
              IR.FConst(2.0))
gid += 3

rel = IR.BE('*', gid+2,
            IR.FConst(-2.0), 
            IR.BE('*', gid+1,
                  temp0,
                  IR.UE('sin', gid, temp1)))
gid += 3

IR.TuneExpr(rel) 
