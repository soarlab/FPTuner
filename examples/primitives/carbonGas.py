
import tft_ir_api as IR

var_T = IR.RealVE("T", 0, float(300.0)-float(0.01), float(300.0)+float(0.01))
var_a = IR.RealVE("a", 1, float(0.401)-float(1e-06), float(0.401)+float(1e-06))
var_b = IR.RealVE("b", 2, float(42.7e-06)-float(1e-10), float(42.7e-06)+float(1e-10))
var_N = IR.RealVE("N", 3, float(995.0), float(1005.0))
var_p = IR.FConst(float(3.5e7))
var_V = IR.RealVE("V", 4, float(0.1)-float(0.005), float(0.5)+float(0.005))
const_k = IR.FConst(float(1.3806503e-23))

temp0 = IR.BE("/",  5, var_N, var_V)

sub0 = IR.BE("*",  6, temp0, temp0)
sub1 = IR.BE("-",  7, var_V, IR.BE("*",  8, var_N, var_b))
sub2 = IR.BE("*",  9, IR.BE("+", 10, var_p, IR.BE("*", 11, var_a, sub0)), sub1)
sub3 = IR.BE("*", 12, IR.BE("*", 13, const_k, var_N), var_T)

rel = IR.BE("-", 14, sub2, sub3)

IR.TuneExpr(rel)

IR.ToFPCore(rel, "carbonGas.fpcore")
