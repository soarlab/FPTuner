
import tft_ir_api as IR

delta = 1e-08 

var_x1 = IR.RealVE("x1", 0, (-15.0 - delta), (15.0 + delta))     
var_x2 = IR.RealVE("x2", 1, (-15.0 - delta), (15.0 + delta)) 
var_x3 = IR.RealVE("x3", 2, (-15.0 - delta), (15.0 + delta)) 
    
sub_x1x2 = IR.BE("*",  3, var_x1, var_x2)     
sub_x2x3 = IR.BE("*",  5, var_x2, var_x3) 
    
r1_sub0 = IR.UE("-",  7, sub_x1x2) 
r1_sub1 = IR.BE("*",  8, IR.FConst(2.0), sub_x2x3) 
r1 = IR.BE("-", 11, IR.BE("-", 10, IR.BE("-",  9, r1_sub0, r1_sub1), var_x1), var_x3)

rs = r1 

IR.TuneExpr(rs) 
