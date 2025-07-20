ch=input("Enter hex value ")
dec=int(ch,16)
i=0
s=0
while dec>0:
    r=dec%8
    s=s+r*(10**i)
    i=i+1
    dec=dec//8
print("Octal value is",s)
