
import os
import sys
import time 
import signal 
from fractions import Fraction 
import subprocess as subp 
import tft_utils 
import tft_expr 
import tft_error_form 
from multiprocessing import Queue 

# ==== global variables =====
NAME_QUERY         = "__tft_gelpia_query" 
FNAME_GELPIA_QUERY = os.path.abspath(NAME_QUERY) 
FNAME_GELPIA_LOG   = os.path.abspath("__tft_gelpia_log") 


SAVE_QUERY        = False 
DIR_SAVED_QUERIES = "saved-gelpia-queries" 


# TIMEOUT = 10
# TIMEOUT = 60  
TIMEOUT = 120 
# TIMEOUT = 600 
POLL_INTERVAL = 0.01 

# DEFAULT_TOLERANCE=1e0
DEFAULT_TOLERANCE=1e-01 
# DEFAULT_TOLERANCE=1e-04 
# DEFAULT_TOLERANCE=1e-14

VERBOSE = False 

MAX_RETRIES = 10 


# ========
# class definition 
# ========
class GelpiaSolver : 
    tolerance = None 
    cached_result = None 

    def __init__ (self, tolerance=DEFAULT_TOLERANCE): 
        self.tolerance = tolerance 
        self.cached_result = None 

    def maxObj (self, expr_optobj, id_query=None, id_retry=None): 
        assert(isinstance(expr_optobj, tft_expr.Expr)) 
        assert(self.tolerance is not None) 
        assert((id_query is None) or (type(id_query) is int)) 
        assert((id_retry is None) or (type(id_retry) is int)) 
        
        tft_utils.checkGelpiaInstallation("master") 

        if ((id_retry is not None) and (id_retry >= MAX_RETRIES)): 
            print("WARNING: Gelpia reached the max. # of retries...") 
            return None 

        self.cached_result = None 
 
        fname_query = os.path.abspath(FNAME_GELPIA_QUERY) 
        fname_log   = os.path.abspath(FNAME_GELPIA_LOG) 
        if (id_query is not None): 
            fname_query = fname_query + "." + str(id_query) 
            fname_log   = fname_log   + "." + str(id_query) 
        if (VERBOSE): 
            if (os.path.isfile(fname_query)): 
                print ("WARNING: automatically overwrite Gelpia's query file: " + fname_query) 
            if (os.path.isfile(fname_log)):
                print ("WARNING: automatically overwrite Gelpia's log file: " + fname_log) 

        # ---- write query file ----
        qfile = open(fname_query, "w") 

        # write input and output tolerances 
        qfile.write("-ie .0000000001\n")

        qfile.write("-oe " + str(float(self.tolerance)) + "\n") 

        # maximization objective 
        qfile.write("-f \"" + expr_optobj.toCString() + "\"\n") 

        # specify the timeout
        qfile.write("-t " + str(TIMEOUT) + "\n") 

        # turn off divide-by-zero analysis
        qfile.write("-z\n") 

        # redirect temporal results to stderr 
        qfile.write("-L " + fname_log + "\n") 

        # variables and their ranges 
        str_vars = "-i \"{" 
        if (len(expr_optobj.vars()) == 0): 
            str_vars = str_vars + "}\"\n"
        else:
            for var in expr_optobj.vars(): 
                assert(isinstance(var, tft_expr.VariableExpr)) 
                assert(var.hasBounds()) 
                if (var.type() is Fraction):
                    str_vars = str_vars + "\'" + var.label() + "\' : (" + var.lb().toCString() + "," + var.ub().toCString() +"), "

                elif (var.type() is int): 
                    vlb = var.lb().value()
                    vub = var.ub().value() 
                    assert((vlb == int(vlb)) and (vub == int(vub))) 
                    vlb = int(vlb) 
                    vub = int(vub) 

                    str_vars = str_vars + "\'" + var.label() + "\' : (" + str(vlb) + "," + str(vub) +"), "

                else: 
                    sys.exit("ERROR: Gelpia doesn't support variable type: " + str(var.type())) 

            assert(str_vars.endswith(", ")) 

            str_vars = str_vars[0:len(str_vars)-2] + "}\"\n" 

        qfile.write(str_vars)
        
        qfile.close() 

        # ---- save the query file ---- 
        if (SAVE_QUERY): 
            qi = 0 

            if (not os.path.isdir(DIR_SAVED_QUERIES)): 
                os.system("mkdir " + DIR_SAVED_QUERIES) 
                assert(os.path.isdir(DIR_SAVED_QUERIES)) 

            assert(os.path.isfile(FNAME_GELPIA_QUERY)) 
            
            while (True): 
                qname = DIR_SAVED_QUERIES + "/" + NAME_QUERY + "_" + str(qi) 
                
                if (not os.path.isfile(qname)): 
                    os.system("cp " + FNAME_GELPIA_QUERY + " " + qname) 
                    break 

                else: 
                    qi = qi + 1 

        # ---- run gelpia ---- 
        assert(TIMEOUT > 0) 
        assert((0 < POLL_INTERVAL) and (POLL_INTERVAL <= TIMEOUT)) 

        now_dir = os.path.abspath(os.getcwd()) 
        os.chdir(os.environ["HOME_GELPIA"]) 

        exe_gelpia = subp.Popen([os.environ["GELPIA"], "@"+fname_query], 
                                shell=False, 
                                stdout=subp.PIPE, 
                                stderr=subp.PIPE, bufsize=0)

        finished = False 
        wait_time = 0 
        while (True): 
            time.sleep(POLL_INTERVAL) 
            wait_time = wait_time + POLL_INTERVAL 

            if (exe_gelpia.poll() is not None): 
                finished = True 
                break 

            if (wait_time >= (TIMEOUT + 15)): 
                break 

        os.chdir(now_dir)

        if (not finished) : 
            print ("WARNING: Manually timeout Gelpia... Gelpia's timeout facility may failed...") 

        # ---- read result ----
        not_certain = False 
        value_bound = None 

        if (finished): # Gelpia terminated itself 
            for aline in exe_gelpia.stdout: 
                aline = aline.decode(encoding='UTF-8').strip() 

                if (VERBOSE): 
                    print ("Gelpia: " + aline) 

                if (aline == "error"): 
                    print ("WARNING: Gelpia returned \"error\"") 
                    return None

                if (aline == "ERROR: Division by zero"): 
                    print ("ERROR: Encounter division by zero") 
                    assert(False) 

                str_val = None 

                if   (aline.startswith("[[")): 
                    i_first_end = aline.find("]") 

                    if (i_first_end >= 5): 
                        aline = aline[2:i_first_end] 

                        i_coma = aline.find(",") 
                        
                        if (i_coma >= 1): 
                            str_val = aline[i_coma+1:]

                elif (aline.startswith("[") and aline.endswith(", {")): 
                    str_val = aline[1:len(aline)-3] 

                elif (aline.startswith("[") and aline.endswith(", {}]")): 
                    str_val = aline[1:len(aline)-5] 

                else: 
                    pass 
            
                if (str_val is not None):
                    if (str_val == "inf" or str_val == "nan"): 
                        print ("WARNING: pessimistic bound: " + str_val) 
                        print ("   expr: " + str(expr_optobj.toCString())) 
                        print ("Gelpia retry...") 

                        if (id_retry is None): 
                            return self.maxObj(expr_optobj, id_query, 1) 
                        else: 
                            assert(type(id_retry) is int) 
                            return self.maxObj(expr_optobj, id_query, (id_retry + 1)) 

                    try: 
                        value_bound = Fraction(float(str_val)) 
                    except: 
                        print ("WARNING: cannot convert " + str_val + " to float...") 
                        return None 
            
            if (value_bound is None): 
                not_certain = True 
                print ("WARNING: Gelpia didn't return a certain answer...") 
            # assert(value_bound is not None) 

        if (not finished or not_certain):  # 1) Gelpia didn't terminate itself OR 2) Gelpia didn't return a certain answer... 
            if (not finished): 
                exe_gelpia.terminate()
                exe_gelpia.kill() 
            
            assert(os.path.isfile(fname_log)) 
            flog = open(fname_log, "r") 

            target_token = "guaranteed ub:"

            for aline in flog: 
                if (type(aline) is not str):
                    aline = aline.decode(encoding='UTF-8').strip() 

                if (VERBOSE): 
                    print ("Gelpia (stderr) >> " + aline) 

                target_id = aline.find(target_token) 

                if (target_id >= 0): 
                    aline = aline[target_id+len(target_token) : ].strip() 

                    try: 
                        value_bound = Fraction(float(aline)) 
                    except: 
                        print ("WARNING: cannot convert " + aline + " to float...") 

                        sys.exit(1) 

            flog.close() 

            if (value_bound is None): 
                print ("WARNING: Gelpia terminated prematurely... retry...") 

                if (id_retry is None): 
                    return self.maxObj(expr_optobj, id_query, 1) 
                else: 
                    assert(type(id_retry) is int) 
                    return self.maxObj(expr_optobj, id_query, (id_retry + 1)) 

        if (value_bound is None): 
            print ("EXIT: Gelpia abort with value_bound = None...") 
            print (":: " + str(expr_optobj)) 
            sys.exit(1) 

        # ---- finalize ---- 
        self.cached_result = value_bound 
        return value_bound

        
        
        
        
    
        
    
