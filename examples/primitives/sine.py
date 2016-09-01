
import tft_ir_api as IR 

x = IR.RealVE("x", 0, -1.57079632679, 1.57079632679)

x2 = IR.BE("*", 1, x, x) 
x3 = IR.BE("*", 2, x2, x) 

rel = None 

x5 = IR.BE("*", 3, x2, x3) 
x7 = IR.BE("*", 4, x2, x5) 

rel_1 = IR.BE("/", 5, x3, IR.FConst(6.0)) 
rel_2 = IR.BE("/", 6, x5, IR.FConst(120.0)) 
rel_3 = IR.BE("/", 7, x7, IR.FConst(5040.0)) 

rel = IR.BE("-", 10, IR.BE("+", 9, IR.BE("-", 8, x, rel_1), rel_2), rel_3) 

IR.TuneExpr(rel) 
    

