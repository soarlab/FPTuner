<h1> FPTuner: Rigorous Floating-point Mixed Precision Tuner </h1> 



# Installation 

## Reguired applications 

- git 

- Python3 
    - FPTuner currently supports python3 only. We strongly recommend setting **python** command to be an alias of **python3**. 

- OCaml 4.0 or later
    - This is required by FPTaylor, an underlying floating-point error estimation tool used by FPTuner. (FPTaylor will be installed automatically by the installation script described later.) 

- Gurobi v6.5 
    - Please go to <a href=http://www.gurobi.com/>Gurobi website</a> and follow the installation instructions. It is free for academic use (the academic license is free). 
    - Add the path of Gurobi's python module to environment variable **PYTHONPATH**. For example, 
        - Assume that Gurobi is install under **/home/myname/gurobi650/linux64**.  
        - There should be a directory similar to **/home/myname/gurobi650/linux64/lib/python3.4_utf32**. 
        - Add path (under bash) with
	      ```
	      export PYTHONPATH=/home/myname/gurobi650/linux64/lib/python3.4_utf32:$PYTHONPAH
	      ```


## How to install? 

1. Acquire FPTuner from our github repository: 
    ```
    git clone https://github.com/soarlab/FPTuner
    ```
2. Go to the root directory of FPTuner. E.g., 
    ```
    cd ./FPTuner
    ```
3. Run the setup script **at the root directory of FPTuner**: 
    ```
    python setup.py install 
    ```
4. Set up the required environment variables. 
The installation script used in the previous step will print out the instruction of setting up the related environment variables. 
Please follow the instruction for the setup. 



# Using FPTuner 
To test the installation, please try out the hello-world example through the following steps: 

1. Go to directory **src** under the root of FPTuner. 

2. Run command 
    ```
    python3 ./fptuner.py -e 0.001 ../examples/helloworld0.py
    ```
The console output of FPTuner should be the following: 
```
==== error bound : 0.001 ====
---- alloc. ----
Group 0 : 32-bit
Group 1 : 32-bit
Group 2 : 64-bit
Group 3 : 64-bit
Group 4 : 64-bit
----------------

# L2H castings: 2
# H2L castings: 0
# Castings: 2
```
In addition, a .cpp file **helloworld0.0.001.cpp** will be generated. 
Now we describe how to use FPTuner with this hello-world example. 


## Input 
FPTuner takes an expression specification and an user-specified error threshold for generating the optimal allocation. 
In the command ```python3 ./fptuner.py -e 0.001 ../examples/helloworld0.py```, file **helloworld0.py** is the expression specification and **-e 0.001** specifies 1e-03 as the error threshold. 

The later section "**Example of Expression Specification**" describes how to specify the expression through the python-based interface. 


## Output
FPTuner prints the allocation on console. 
In the example output, for example, 
```
Group 0 : 32-bit
```
denotes that the group 0 (gang 0) operators are assigned 32-bit. 
**# L2H castings** (resp., **# H2L castings**) indicates the number of low-to-high (resp., high-to-low) type casts in this allocation. 
**# Castings** is the summation of **# L2H castings** and **# H2L castings**. 
In addition to the console output, a .cpp file is synthesized by FPTuner which implements the allocation. 


## Reference
The complete reference of FPTuner is given in <a href="https://github.com/soarlab/FPTuner/blob/master/Reference.md">Reference.md</a>. 


## Advance usages
Based on this hello-world example, we introduce some more tuning options provided by FPTuner.
 
### Candidate bit-widths
FPTuner tunes for mixed 32- and 64-bit by default. 
Tuning for mixed 64- and 128-bit can be done with option 
```
-b "64 128"
```
FPTuner currently supports tuning for the following three bit-width candidate sets: 
- 32- and 64-bit (specified with ```-b "32 64"```)
- 64- and 128-bit (specified with ```-b "64 128"```)
- 32-, 64-, and 128-bit (specified with ```-b "32 64 128"```) 

### Multiple error thresholds
FPTuner can take multiple error thresholds and generate the optimal allocation of each threshold. 
For example, the following option results in two allocations generated for the two error thresholds (0.001 and 0.0001): 
```
-e "0.001 0.0001
```



# Running the Benchmarks 
FPTuner is evaluated with a set of benchmarks. 
Similar to the hello-world example, we can run each of the benchmarks with the following command (under directory **src**): 
```
python3 ./fptuner.py -e "0.001 0.0001" -b "32 64" path-to-the-benchmark
```
(The desired error thresholds and the bit-width candidates are specified with options -e and -b respectively.) 
The following table offers the benchmark names and their relative paths to the root directory of FPTuner. 

**Benchmark Name** | **Relative Path to the Root of FPTuner** 
sine         | examples/primitives/sine.py
sqroot       | examples/primitives/sqroot.py
sineOrder3   | examples/primitives/sineOrder3.py 
predatorPrey | examples/primitives/predatorPrey.py
verhulst     | examples/primitives/verhulst.py
rigidBody 1  | examples/primitives/rigidBody-1.py
rigidBody 2  | examples/primitives/rigidBody-2.py
turbine 1    | examples/primitives/turbine-1.py
turbine 2    | examples/primitives/turbine-2.py
turbine 3    | examples/primitives/turbine-3.py
doppler 1    | examples/primitives/doppler-1.py
doppler 2    | examples/primitives/doppler-2.py
doppler 3    | examples/primitives/doppler-3.py
carbonGas    | examples/primitives/carbonGas.py 
jet          | examples/primitives/jet.py



# Example of Expression Specification
FPTuner decides the optimal bit-widths of the operators in the floating-point implementations of real-number computations.

At this point, FPTuner provides a Python interface that allows the users to specify their the real-number computations. 
In this section, we introduce how to use the Python interface through a simple example: 
```
(A + B) * C
```
which is the *hello-world 0* example. 


## Invoke the interface module 
- In a python (.py) file, use the following line to invoke the interface module: 
    ```
    import tft_ir_api as IR
    ```

- Note that the **src** directory under the FPTuner root directory should be added to the environment variable **PYTHONPATH**. 


## Declare bounded variables
FPTuner currently supports variables which have bounded and contiguous ranges. 
For example, we want to declare three variables, A, B, and C, and assign [0.0, 100.0] as their ranges. 
This can be achieved with function **IR.RealVE** as shown in the following lines: 
```
A = IR.RealVE("A", 0, 0.0, 100.0) 
B = IR.RealVE("B", 1, 0.0, 100.0) 
C = IR.RealVE("C", 2, 0.0, 100.0) 
```
Function **IR.RealVE** returns a variable (variable expression) with taking four arguments: 

1. The label of the variable. 

2. The group ID of the variable. 
Expressions assigned with the same group (gang) ID will be assigned with the same bit-width. 
In this example, we assume that we want to assign different bit-widths to the variables. 
Thus, the three variables have different ID: A has 1, B has 2, and C has 3.

3. The lower bound of the value range. 

4. The upper bound of the value range. 


## Specify binary expressions 
There are two binary expressions in our example, and they can be specified with function **IR.BE** as shown in the following line: 
```
rel = IR.BE("*", 4, IR.BE("+", 3, A, B), C) 
```

The application 
```
IR.BE("+", 3, A, B)
``` 
results in a binary expression ```(A + B)```. 
The four arguments are explained as follows: 

1. The first argument is a string which specifies the binary operator. 
In this case, "+" specifies the addition. 

2. The second argument is an integer which gives the group ID. 
Expressions having the same group ID will be assigned with the same bit-width. 

3. The third argument is the left-hand-side operand. 
In this case, it is variable A. 

4. The forth argument is the right-hand-side operand. 
In this case, it is variable B. 

Similarly, 
``` 
IR.BE("*", 4, IR.BE("+", 3, A, B), C) 
```
returns expression 
```
(A + B) * C
```


## Tune for expression (A + B) * C
To assign ```(A + B) * C``` to FPTuner as the tuning target, we use the following line: 
```
IR.TuneExpr(rel)
``` 

**rel** is the reference of our targeted expression. 
Function **IR.TuneExpr** specifies the expression to tune. 



# Acknowledgements 
Supported in part by NSF grants 1643056, 1421726, and 1642958. 