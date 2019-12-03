
import tft_ir_api as IR

A = IR.RealVE("A", 0, 0.0, 100.0)
B = IR.RealVE("B", 1, 0.0, 100.0)
C = IR.RealVE("C", 2, 0.0, 100.0)

rel = IR.BE("*", 4, IR.BE("+", 3, A, B), C)

IR.TuneExpr(rel)
