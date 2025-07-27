s=input("Enter string ")
i=int(input("Enter a position "))
r=""
for j in range(len(s)):
    if i!=j:
        r=r+s[j]
    else:
        r=r+""
print(r)
