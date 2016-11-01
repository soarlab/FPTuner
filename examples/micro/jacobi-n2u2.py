import tft_ir_api as IR

n = 2

unrolls = 2

low  =   1.0
high = 10.0


A = list()
for j in range(n):
    row = list()
    for i in range(n):
        row.append(IR.RealVE("a{}{}".format(i,j), 0, low, high))
    A.append(row)


b = list()
for i in range(n):
    b.append(IR.RealVE("b{}".format(i), 1, low, high))


x = list()
for i in range(n):
    x.append(IR.FConst(1.0))

g=2

#j k = 0
#j while convergence not reached: # while loop
for k in range(unrolls): # replacement for while loop
    for i in range(n): # i loop
        sigma = IR.FConst(0.0)
        for j in range(n): # j loop
            if j != i:
                sigma = IR.BE("+", g, sigma, IR.BE("*", g, A[i][j], x[j]))
                g += 1
        # end j loop
        x[i] = IR.BE("/", g, IR.BE("-", g, b[i], sigma), A[i][j])
        g += 1
    # end i loop
#j check convergence
#j k = k+1
# end while loop

print(x[0])
rs = x[0]
IR.TuneExpr(rs)
