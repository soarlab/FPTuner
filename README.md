<h1> FPTuner: Rigorous Floating-point Mixed Precision Tuner </h1> 



# Installation 
- FPTuner has been tested on Ubuntu 12.04, 14.04, 16.04 on x86_64


## Requirements

- git 
- python3 
    - FPTuner currently supports python3 only.
- PLY for python3
- bison
- flex
- ocaml
- g++

On Ubuntu these can all be installed with
```
sudo apt-get isntall -y git python3-ply bison flex ocaml g++
```


- Gurobi v6.5. Note that FPTuner's installation script **does not** automatically install Gurobi. Please follow the following stpes to install Gurobi and acquire a free academic license. 
    - Installation. 
        - On <a href="www.gurobi.com">www.gurobi.com</a> tab "DOWNLOADS," select "Download Center." 
        - Select "Gurobi Optimizer." You need to register an account for the academic licenses also. 
        - Download "gurobi6.5.2_linux64.tar.gz" and untar with ``tar -xvf gurobi6.5.2_linux64.tar.gz``
        - ``cd gurobi652/linux64`` and ``./setup.py build``
    - Set environment variables as the following example commands work under bash: 
        ```
        export GUROBI_HOME=your-path/gurobi652/linux64
        export PATH=$GUROBI_HOME/bin:$PATH
        export LD_LIBRARY_PATH=$GUROBI_HOME/lib:$LD_LIBRARY_PATH
        ```
    - Acquire an academic license. 
        - Go to <a href="https://user.gurobi.com/download/licenses/free-academic">https://user.gurobi.com/download/licenses/free-academic</a>
        - Read the User License Agreement and the conditions, then click "Request License."  
        - Copy the command "grbgetkey your-activation-code" shown on the screen.
        - Under the **bin** directory of your Gurobi installation, run the grbgetkey command which you just copied. This command will require you to enter a path to store the license key file. The grbgetkey command will indicate you to setup environment variable **GRB_LICENSE_FILE** to a path to the license file.
    - After the installation, add the path of Gurobi's python module to environment variable **PYTHONPATH**. For example, 
        - Assuming Gurobi is installed under **/home/myname/gurobi652/linux64**.  
	    - **Note**: the version of Gurobi is assumed to be 6.5.2; your Gurobi path may be different.
        - There should be a directory similar to **/home/myname/gurobi652/linux64/lib/python3.4_utf32**.
	    - **Note**: type ```python3 --version``` to find the version on your system. If it is Python 3.5, use 
	    ***/home/myname/gurobi652/linux64/lib/python3.5_utf32*** instead.
        - Add this to your environment (under bash) with
	
	      ```
	      export PYTHONPATH=/home/myname/gurobi652/linux64/lib/python3.4_utf32:$PYTHONPATH
	      export LD_LIBRARY_PATH=/home/myname/gurobi652/linux64/lib/:$LD_LIBRARY_PATH
	      ```
    - For more installation details, please refer to the <a href="http://www.gurobi.com/documentation/6.5/quickstart_linux.pdf">user menu</a>. 


## How to install FPTuner? 

1. Download FPTuner from our github repository: 
    ```
    git clone https://github.com/soarlab/FPTuner
    ```
2. Go to the root directory of FPTuner. E.g., 
    ```
    cd ./FPTuner
    ```
3. Run the setup script **at the root directory of FPTuner**: 
    ```
    python3 setup.py install 
    ```
4. Set up the required environment variables. 
The installation script used in the previous step will create a file ```fptuner_vars``` for setting up the related environment variables under bash. To do so, run
```
source fptuner_vars
```

Please follow the instruction for the setup.

### To uninstall, run
```
python3 setup.py uninstall 
```



# Using FPTuner 
To test the installation, please try out the hello-world example through the following steps: 

1. Go to directory **bin** under the root of FPTuner. 

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
FPTuner prints the allocation on the console. 
In the example output, for example, 
```
Group 0 : 32-bit
```
denotes that the group 0 (gang 0) operators are assigned 32-bit precision. 
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
-e "0.001 0.0001"
```



# To POPL Artifact Evaluation Reviewers
## Reproduce the tuning results of Table 5.1 and Table 5.2
The tuning results of Table 5.1 are shown under column "# of double-ops forced by Es" and the results of Table 5.2 are shown under column "# of single-ops forced by Es." 
With a correct installation of FPTuner (e.g., the above hello-world example works), the fastest way to reproduce the two tables is using the scripts under directory **bin**. 

For Table 5.1, please run (under directory **bin**) 
```
./test-table-5.1
```

For Table 5.2, please run (under directory **bin**)
```
./test-table-5.2
```


## Performance and energy measurements
We currently don't offer the scripts to automatically measure performance and energy. 
However, as demonstrated through the hello-world example, the .cpp files of the corresponding mixed precision allocations are offered. 
You can freely do performance and energy measurements with those .cpp files on your platforms. 


## Tuning results and tuning performance may be affected by global optimization
The tuning results and the tuning performance of FPTuner are affected by the underlying global optimization. 
The global optimization may calculate tight bounds (resp., loose bounds) of the first derivatives that result in more (resp., fewer) low-precision operators. 
In addition, FPTuner's performance is currently dominated by global optimization. 
Consequently, there may be tuning results which don't exactly match results shown in the paper. 


## Individually running the Benchmarks 
Similar to the hello-world example, we can run each of the benchmarks with the following command (under directory **bin**): 
```
python3 ./fptuner.py -e "0.001 0.0001" -b "32 64" path-to-the-benchmark
```
(The desired error thresholds and the bit-width candidates are specified with options -e and -b respectively.) 
The following table offers the benchmark names and their relative paths to the root directory of FPTuner. 

| **Benchmark Name** | **Relative Path to the Root of FPTuner** |
|--------|--------|
| sine         | examples/primitives/sine.py | 
| sqroot       | examples/primitives/sqroot.py | 
| sineOrder3   | examples/primitives/sineOrder3.py | 
| predatorPrey | examples/primitives/predatorPrey.py |
| verhulst     | examples/primitives/verhulst.py |
| rigidBody 1  | examples/primitives/rigidBody-1.py |
| rigidBody 2  | examples/primitives/rigidBody-2.py |
| turbine 1    | examples/primitives/turbine-1.py |
| turbine 2    | examples/primitives/turbine-2.py |
| turbine 3    | examples/primitives/turbine-3.py |
| doppler 1    | examples/primitives/doppler-1.py |
| doppler 2    | examples/primitives/doppler-2.py |
| doppler 3    | examples/primitives/doppler-3.py |
| carbonGas    | examples/primitives/carbonGas.py |
| jet          | examples/primitives/jet.py |
| cone-area    | examples/math/cone-area.py |
| Gaussian     | examples/math/gaussian.py |
| Maxwell-Boltzmann | examples/math/maxwell-boltzmann.py |
| reduction    | examples/micro/reduction.py |




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

4. The fourth argument is the right-hand-side operand. 
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
