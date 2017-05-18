
import tft_ir_api as IR 

gid = 0

x = IR.VE('x', gid, -1.0 1.0)
gid += 1

temp0 = IR.UE('log', gid+1, IR.BE('-', gid  , IR.FConst(1.0), x))
temp1 = IR.UE('log', gid+3, IR.BE('+', gid+2, IR.FConst(1.0), x))
gid += 4

rel = IR.BE('/', gid, temp0, temp1)
gid += 1


IR.TuneExpr(rel) 

