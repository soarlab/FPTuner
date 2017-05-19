
import tft_ir_api as IR


def sube (g, A, E):
    tmp0 = IR.BE('*', g, A, E)
    tmp1 = IR.UE('exp', g+1, tmp0)
    tmp2 = IR.BE('-', g+2, tmp1, IR.FConst(1.0))

    return (g+3), tmp2


# ====
# main
# ====

gid = 0

a = IR.RealVE('a', gid  , -1.0, 1.0)
b = IR.RealVE('a', gid+1, -1.0, 1.0)
e = IR.RealVE('e', gid+2, -1.0, 1.0)
gid += 3

temp0  = IR.BE('+', gid  , a, b)
gid += 1
gid, temp1 = sube(gid, temp0, e)
temp2 = IR.BE('*', gid, e, temp1)
gid += 1

gid, temp3 = sube(gid, a, e)
gid, temp4 = sube(gid, b, e)
temp5 = IR.BE('*', gid, temp3, temp4)
gid += 1

rel = IR.BE('/', gid, temp2, temp5)
gid += 1


IR.TuneExpr(rel) 

