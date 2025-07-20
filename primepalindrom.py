n1=int(input("Enter n1 "))
n2=int(input("Enter n2 "))
n=n1
s=0
while n<=n2:
    d=2
    is_prime=1
    while d<n:
        if n%d==0:
            is_prime=0
        d=d+1
    if is_prime==1:
        if n>1:
            t=n
            s=0
            while t>0:
                r=t%10
                s=(s*10)+r
                t=t//10
            if s==n:
                print(n)
    n=n+1
