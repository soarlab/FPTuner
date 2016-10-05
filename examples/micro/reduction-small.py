
import tft_ir_api as IR 
import tft_ir_backend 
import math

alen     = 16
vlb      = -100.0 
vub      = 100.0 

gid_data = 0 

assert(alen > 0) 
assert(vlb < vub)
assert(math.log(alen, 2) == int(math.log(alen, 2)))

n_stages = int(math.log(alen, 2))

arr = [IR.RealVE("v"+str(i), gid_data, vlb, vub) for i in range(0, alen)] 

for i_stage in range(1, (n_stages+1)) : 
    l_arr = len(arr) 
    assert(l_arr % 2 == 0) 
    l_arr = int(l_arr / 2) 
    
    for i in range(0, l_arr): 
        arr[i] = IR.BE("+", i_stage, arr[i], arr[i+l_arr]) 

    arr = arr[0:l_arr] 

assert(len(arr) == 1) 

IR.SetGroupWeight(gid_data, 16.0) 

IR.TuneExpr(arr[0]) 


