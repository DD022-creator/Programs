a=int(input("Enter a "))
b=int(input("Enter b "))
c=int(input("Enter c "))
if a==b==c:
    print("a,b,c are equal")
elif a>b==c:
    print("b and c are equal and a is greater than b and c")
elif b>c==a:
    print("a and c are equal and b is greater than a and c")
elif c>b==a:
    print("a and b are equal and c is greater than a and b")
elif b==c>a:
    print("b and c are equal and greater than a")
elif c==a>b:
    print("a and c are equal and greater than b")
elif b==a>c:
    print("a and b are equal and greater than c")
elif a>b:
    if a>c:
        print("a is greater than b and c")
    else:
        print("c is greater than a and b")
else:
    if b>c:
        print("b is greater than a and c")
    else:
        print("c is greater than a and b")
    
