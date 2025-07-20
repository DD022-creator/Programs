n1=int(input("Enter n1 "))
n2=int(input("Enter n2 "))
n=n1
print("Twisted primes")
while n<=n2:
    is_prime=1
    d=2
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
            d1=2
            while d1<s:
                if s%d1==0:
                    is_prime=0
                d1=d1+1
            if is_prime==1:
                print(n,s)
    n=n+1
        
