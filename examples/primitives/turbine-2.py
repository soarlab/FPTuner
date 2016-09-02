
import tft_ir_api as IR

var_v = IR.RealVE("v", 0, (-4.5 - 0.0000001), (-0.3 + 0.0000001)) 
var_w = IR.RealVE("w", 1, (0.4 - 0.000000000001), (0.9 + 0.000000000001)) 
var_r = IR.RealVE("r", 2, (3.8 - 0.00000001), (7.8 + 0.00000001)) 

sub_1v     = IR.BE("-",  3, IR.FConst(1.0), var_v) 
    
sub_ww     = IR.BE("*",  4, var_w, var_w) 
    
sub_rr     = IR.BE("*",  5, var_r, var_r) 
    
sub_wwrr   = IR.BE("*",  7, sub_ww, sub_rr) 
    
sub_wwrr1v = IR.BE("/",  8, sub_wwrr, sub_1v) 

r2_sub0    = IR.BE("*", 16, IR.FConst(6.0), var_v) 
r2_sub1    = IR.BE("*", 18, IR.BE("*", 17, IR.FConst(0.5), var_v), sub_wwrr1v) 
r2         = IR.BE("-", 20, IR.BE("-", 19, r2_sub0, r2_sub1), IR.FConst(2.5)) 

rs = r2 

IR.TuneExpr(rs) 
