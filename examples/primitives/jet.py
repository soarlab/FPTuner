
import tft_ir_api as IR

var_x1 = IR.RealVE("x1", 0, -5.0, 5.0)
var_x2 = IR.RealVE("x2", 1, -20.0, 5.0) 

temp0 = IR.BE("*",  2, var_x1, var_x1) # x1^2
temp1 = IR.BE("*",  3, temp0, var_x1) # x1^3

sub2_0 = IR.BE("-",  4, 
               IR.BE("+",  5, 
                     IR.BE("*",  6, IR.FConst(3.0), temp0), 
                     IR.BE("*",  7, IR.FConst(2.0), var_x2)), 
               var_x1) 
sub2_1 = IR.BE("+",  8, temp0, IR.FConst(1.0))
sub2 = IR.BE("/",  9, sub2_0, sub2_1)

sub3_0_0_0 = IR.BE("*", 10, IR.BE("*", 11, IR.FConst(2.0), var_x1), sub2)
sub3_0_0_1 = IR.BE("-", 12, sub2, IR.FConst(3.0))
sub3_0_0 = IR.BE("*", 13, sub3_0_0_0, sub3_0_0_1) 
sub3_0_1 = IR.BE("*", 14, temp0, IR.BE("-", 15, IR.BE("*", 16, IR.FConst(4.0), sub2), IR.FConst(6.0)))
sub3_0 = IR.BE("+", 17, sub3_0_0, sub3_0_1) 
sub3_1 = IR.BE("+", 18, temp0, IR.FConst(1.0))
sub3 = IR.BE("*", 19, sub3_0, sub3_1) 

rel_temp0 = IR.BE("+", 20, IR.BE("+", 21, IR.BE("+", 22, sub3, IR.BE("*", 23, IR.BE("*", 24, IR.FConst(3.0), temp0), sub2)), temp1), var_x1)
rel_temp1 = IR.BE("*", 25, IR.FConst(3.0), sub2) 
rel = IR.BE("+", 26, var_x1, IR.BE("+", 27, rel_temp0, rel_temp1))

IR.TuneExpr(rel) 

IR.ToFPCore(rel, "jet.fpcore")
