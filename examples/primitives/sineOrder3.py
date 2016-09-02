
import tft_ir_api as IR

x = IR.RealVE("x", 0, -2.0, 2.0) 

x2 = IR.BE("*", 1, x, x) 
x3 = IR.BE("*", 2, x2, x) 

rel = None 

rel_1 = IR.BE("*", 20, IR.FConst(0.954929658551372), x) 
rel_2 = IR.BE("*", 21, IR.FConst(0.12900613773279798), x3) 

rel = IR.BE("-", 22, rel_1, rel_2)

IR.TuneExpr(rel) 
