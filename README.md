<h1> FPTuner: Rigorous Floating-point Mixed Precision Tuner </h1> 



# Installation 

## Reguired applications 

- Python3 
    - Your **python** command needs to be an alias of **python3**. 
- git 


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



# Running Toy Examples 
## Toy example 0

1. Go to directory **src** under the root of FPTuner. 

2. Run command 
    ```
    python ./fptuner.py -e 0.00001 ../examples/toy0.py
    ```
The output of FPTuner should be 
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

## Toy example 1 

1. Go to directory **src** under the root of FPTuner. 

2. Run command 
    ```
    python ./fptuner.py -e 0.00004 ../examples/toy1.py
    ```