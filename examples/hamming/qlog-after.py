
import tft_ir_api as IR

gid = 0

x = IR.RealVE('x', gid, -1.0, 1.0)
gid += 1

temp0 = IR.BE('+', gid  , IR.FConst(1.0), x) # (+ 1.0 x)
temp1 = IR.BE('*', gid+1, x, x) # (sqr x)
temp2 = IR.BE('*', gid+2, IR.FConst(0.5), temp1) # (* 0.5 (sqr x))
temp3 = IR.BE('+', gid+3, temp2, temp0)
gid += 4

rel = IR.BE('*', gid, IR.FConst(-1.0), temp3)
gid += 1


IR.TuneExpr(rel)
