<h1> FPTuner: Rigorous Floating-point Mixed Precision Tuner </h1> 



# Installation 

## Reguired applications 

- Python3 
    - Your **python** command needs to be an alias of **python3**. 

- git 

- Gurobi v6.5 
    - Go to <a href=http://www.gurobi.com/>Gurobi website</a> and follow the installation instructions. 
    - Add the path of Gurobi's python module to environment variable **PYTHONPATH**. For example, 
        - Gurobi is install under **/home/myname/gurobi650/linux64**. (The Academic License is free.) 
        - There should be a directory similar to **/home/myname/gurobi650/linux64/lib/python3.4_utf32**. 
        - Add path (under bash) by 
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



# Running Hello-world Examples 
## Hello-world example 0

1. Go to directory **src** under the root of FPTuner. 

2. Run command 
    ```
    python ./fptuner.py -e 0.00001 ../examples/helloworld0.py
    ```
The output of FPTuner should be the following: 
```
-- ensure M2 --
Total Error:     7.629395e-06
Total M2:        1.694066e-21
Error Threshold: 1e-05
---------------
==== error bound : 1e-05 ====
---- alloc. ----
Score: 2.0
-- GIDs --
ErrorTerm(gid: 0) => EPSILON_32
ErrorTerm(gid: 1) => EPSILON_32
ErrorTerm(gid: 2) => EPSILON_64
ErrorTerm(gid: 3) => EPSILON_64
ErrorTerm(gid: 4) => EPSILON_64
----------------

# L2H castings: 2
# H2L castings: 0
# Castings: 2
```

## Hello-world example 1 

1. Go to directory **src** under the root of FPTuner. 

2. Run command 
    ```
    python ./fptuner.py -e 0.00004 ../examples/helloworld1.py
    ```
The output of FPTuner should be the following: 
```
-- ensure M2 --
Total Error:     1.954973e-05
Total M2:        4.547474e-13
Error Threshold: 4e-05
---------------
==== error bound : 4e-05 ====
---- alloc. ----
Score: 2.0
-- GIDs --
ErrorTerm(gid: 0) => EPSILON_32
ErrorTerm(gid: 1) => EPSILON_32
ErrorTerm(gid: 2) => EPSILON_64
----------------

# L2H castings: 1
# H2L castings: 0
# Castings: 1
```



# Creating Your Own Examples
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
Expressions assigned with the same group ID will be assigned with the same bit-width. 
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


## Run FPTuner 
**examples/helloworld0.py** shows the above steps of our example. 
With the specification of the real-number computation (described in the Python file **examples/helloworld0.py**), we can now run FPTuner to decide the bit-widths for the operators. 
The following steps tell how to run FPTuner on this example: 

1. Ensure that command **python** is an alias of **python3**. 

2. Choose the desired error threshold. Assume that **0.00005** is chosen. 

3. Go to the **src** directory under the root directory of FPTuner. 

4. Use the following command 
    ```
    python ./fptuner.py -e 0.00005 ../examples/helloworld0.py 
    ```
    - The error threshold is specified with **-e**. 
    - The targeted real-number computation is specified by the last argument which is the path to the Python file. 


## The outputs of FPTuner 


# Command Line Arguments of FPTuner 

## -e 

```
-e [a single floating-point value as the error threshold (absolute error)] 
```
, e.g., 
```
-e 0.0001
```

or 

```
-e "[error theshold 1] [error threshold 2] ..." 
```
, e.g., 
```
-e "0.0001 0.0002 0.0003"
```
Please remember to use quotation marks to enclose the thresholds. 

The later use case is for trying different error thesholds and generate the optimal allocation for each of them. 


## -b 

Use 
```
-b "32 64" 
``` 
to tune with two bit-width candidates, 32-bit and 64-bit. 

Use 
```
-b "64 128" 
``` 
to tune with two candidates, 64-bit and 128-bit. 

Again, please remember to use quotation marks to enclose the bit-widths. 

FPTuner currently supports the above two sets of candidates. 



# Interface Reference 

## RealVE 
### Return 
A variable expression which has a bounded and contiguous value range specified in the arguments. 

### Arguments 

1. The label of the variable. Type: string

2. The group ID of the variable. Type: integer 

3. The lower bound of the value range. Type: floating-point number 

4. The upper bound of the value range. Type: floating-point number 

**Constraints** 

- The lower bound must be less than or equal to the upper bound. 


## BE 
### Return 
A binary expression. 

### Arguments 

1. The binary operator. It is specified by a string which is one of the follows: 
    1. **+** : addition 
    2. **-** : subtraction 
    3. **<em>*</em>** : multiplication 
    4. **/** : division 

2. The group ID. Type: integer 

3. The left-hand-side operand. Type: expression 

4. The right-hand-side operand. Type: expression 



# Acknowledgements 
Supported in part by NSF grants 1643056, 1421726, and 1642958. 