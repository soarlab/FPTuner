
import tft_ir_api as IR 

A = IR.RealVE("A", 0, 0.0, 100.0)
rel = IR.BE("+", 4, A, A) 

IR.TuneExpr(rel) 

