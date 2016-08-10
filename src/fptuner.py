#!/usr/bin/env python 

import os 
import sys 



# ========
# main 
# ========

# ==== get parameters ====
INPUT_FILE  = None 
CONFIG_FILE = "default.fptconf" 

i = 1
while True: 
    if (i >= len(sys.argv)): 
        break 

    arg_in = sys.argv[i] 

    if    (arg_in == "-c"): 
        i = i + 1 
        if (i >= len(sys.argv)): 
            sys.exit("Error: missing configuration file") 

        arg_in      = sys.argv[i] 
        CONFIG_FILE = arg_in

    else: 
        assert(INPUT_FILE is None) 
        INPUT_FILE = arg_in 


    i = i + 1


# ===== check parameters =====
assert(os.path.isfile(INPUT_FILE)) 
assert(INPUT_FILE.endswith(".py")) 

assert(os.path.isfile(CONFIG_FILE)) 





