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

Use 
```
-b "32 64 128"
``` 
to tune with three candidates, 32-bit, 64-bit, and 128-bit. 

Again, please remember to use quotation marks to enclose the bit-widths. 

### Default 
The default of **-b** option is "32 64". 


## -maxc : maximum number of type casts

Use
```
-maxc C
```

to limit up to C type casts in the allocation where C must be an integer.

### Default
Unlimited number of type casts. 



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
