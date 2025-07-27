s=input("Enter string ")
n=len(s)
if n%2==0:
    f=s[:n//2]
    se=s[n//2:]
else:
    f=s[:n//2+1]
    se=s[n//2+1:]
    #print(f,se)
if f==se:
    print("Symmetric")
else:
    print("No")
