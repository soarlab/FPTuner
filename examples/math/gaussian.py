
import math 
import tft_ir_api as IR

gid_data     = 0
gid_data_ave = gid_data
gid_data_dev = gid_data
gid_data_x   = gid_data 

ave = IR.RealVE("ave", gid_data_ave, -1.0, 1.0) 
dev = IR.RealVE("dev", gid_data_dev, 1.0, 3.0) 
x   = IR.RealVE("x",   gid_data_x,   -10.0, 10.0) 

sqrt_2pi = IR.FConst(math.sqrt(2.0 * math.pi)) 

temp3 = IR.BE("*", 3, dev, sqrt_2pi) 
a     = IR.BE("/", 4, IR.FConst(1.0), temp3) 

b = ave 
c = dev 

temp5 = IR.BE("-", 5, x, b) 
temp6 = IR.BE("*", 6, temp5, temp5) 

temp7 = IR.BE("*", 7, IR.FConst(2.0), IR.BE("*", 7, c, c)) 

temp8 = IR.UE("-", 8, IR.BE("/", 8, temp6, temp7)) 
temp9 = IR.UE("exp", 9, temp8) 

rel = IR.BE("*", 10, a, temp9) 

IR.SetGroupWeight(9, 100.0) 

IR.TuneExpr(rel)

