def call(q,r,n):
    if r==n:
        for i in range(n):
            for j in range(n):
                if j == q[i]:
                    print("Q",end=" ")
                else:
                    print("_",end=" ")
            print()
        print("\n\n")
    for i in range(n):
        for j in range(len(q)):
            if i==q[j] or abs(i-q[j]) == abs(r-j):
                break
        else:
            call(q+[i],r+1,n)

a = int(input("Enter n value : "))
call(a)
