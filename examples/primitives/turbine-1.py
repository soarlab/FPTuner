
import tft_ir_api as IR

var_v = IR.RealVE("v", 0, (-4.5 - 0.0000001), (-0.3 + 0.0000001)) 
var_w = IR.RealVE("w", 1, (0.4 - 0.000000000001), (0.9 + 0.000000000001)) 
var_r = IR.RealVE("r", 2, (3.8 - 0.00000001), (7.8 + 0.00000001)) 

sub_1v     = IR.BE("-",  3, IR.FConst(1.0), var_v) 

sub_ww     = IR.BE("*",  4, var_w, var_w) 

sub_rr     = IR.BE("*",  5, var_r, var_r) 

sub_2v     = IR.BE("*",  6, IR.FConst(2.0), var_v) 

sub_wwrr   = IR.BE("*",  7, sub_ww, sub_rr) 

sub_wwrr1v = IR.BE("/",  8, sub_wwrr, sub_1v) 

sub_2rr    = IR.BE("/",  9, IR.FConst(2.0), sub_rr) 

r1_sub0 = IR.BE("*", 12, 
                IR.BE("*", 11, 
                      IR.FConst(0.125), 
                      IR.BE("-", 10, IR.FConst(3.0), sub_2v)), 
                sub_wwrr1v) 

r1 = IR.BE("-", 15, 
           IR.BE("-", 14, 
                 IR.BE("+", 13, IR.FConst(3.0), sub_2rr), 
                 r1_sub0), 
           IR.FConst(4.5)) 

rs = r1 

IR.TuneExpr(rs) 
