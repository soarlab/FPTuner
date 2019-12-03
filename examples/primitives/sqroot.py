
import tft_ir_api as IR

x = IR.RealVE("x", 0, 0.0, 1.0)

x2 = IR.BE("*", 1, x, x)
x3 = IR.BE("*", 2, x2, x)

rel = None

x4 = IR.BE("*", 11, x2, x2)

rel_1 = IR.BE("*", 12, IR.FConst(0.5), x)
rel_2 = IR.BE("*", 13, IR.FConst(0.125), x2)
rel_3 = IR.BE("*", 14, IR.FConst(0.0625), x3)
rel_4 = IR.BE("*", 15, IR.FConst(0.0390625), x4)

rel = IR.BE("-", 19, IR.BE("+", 18, IR.BE("-", 17, IR.BE("+", 16, IR.FConst(1.0), rel_1), rel_2), rel_3), rel_4)

IR.TuneExpr(rel)

IR.ToFPCore(rel, "sqroot.fpcore")
