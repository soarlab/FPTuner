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

## -e : error thresholds 

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

### Default 
There is no default value for **-e** option. 


## -b : candidate bit-widths 

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

USE 
```
-b "32 64 128"
``` 
to tune with three candidates, 32-bit, 64-bit, and 128-bit. 

Again, please remember to use quotation marks to enclose the bit-widths. 

### Default 
The default of **-b** option is "32 64". 



# Interface Reference 

## FConst 
### Return 
A constant expression which bit-width is automatically matched with the operator which consumes the constant. 
(However, for 128-bit operators, the constants are assigned with 64-bit.) 

### Arguments 

1. The value of the constant expression. 


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

1. The binary operator. It is specified by a string which is one of the following:
    1. **+** : addition 
    2. **-** : subtraction 
    3. **<em>*</em>** : multiplication 
    4. **/** : division 

2. The group ID. Type: integer 

3. The left-hand-side operand. Type: expression 

4. The right-hand-side operand. Type: expression 


## UE
### Return 
A unary expression. 

### Arguments
1. The unary operator. It is specified by a string which is one of the following: 
    1. **-** : negation
    2. **exp** : exponential 
    3. **sqrt** : square root

2. The group ID. Type: integer

3. The operand. Type: expression


## SetGroupWeight
This function is for assigning a higher/lower weight to an operator group that allows prioritizing lower/higher bit-width assignments. 

### Return
No return value. 

### Arguments 
1. The group ID. Type: iteger

2. The desired weight. Type: floating-point
