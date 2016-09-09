
import tft_ir_api as IR

delta = 1e-08 

var_x1 = IR.RealVE("x1", 0, (-15.0 - delta), (15.0 + delta))   
var_x2 = IR.RealVE("x2", 1, (-15.0 - delta), (15.0 + delta)) 
var_x3 = IR.RealVE("x3", 2, (-15.0 - delta), (15.0 + delta)) 
    
sub_x1x2   = IR.BE("*",  3, var_x1, var_x2) 
sub_x1x2x3 = IR.BE("*",  4, sub_x1x2, var_x3) 
sub_x3x3   = IR.BE("*",  6, var_x3, var_x3) 
    
r2_sub0 = IR.BE("*", 12, IR.FConst(2.0), sub_x1x2x3) 
r2_sub1 = IR.BE("*", 13, IR.FConst(3.0), sub_x3x3) 
r2_sub2 = IR.BE("*", 14, var_x2, sub_x1x2x3) 

r2 = IR.BE("-", 18, 
           IR.BE("+", 17, 
                 IR.BE("-", 16, 
                       IR.BE("+", 15, r2_sub0, r2_sub1), 
                       r2_sub2), 
                 r2_sub1), 
           var_x2)

rs = r2 

IR.TuneExpr(rs) 
