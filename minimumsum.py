class Solution:
    def minSum(self, arr):
        arr.sort()
        num1 = ""
        num2 = ""
        for i, digit in enumerate(arr):
            if i % 2 == 0:
                num1 += str(digit)
            else:
                num2 += str(digit)
        n1 = int(num1) if num1 else 0
        n2 = int(num2) if num2 else 0

        return str(n1 + n2)
sol=Solution()
print(sol.minSum([6, 8, 4, 5, 2, 3]))   
print(sol.minSum([5, 3, 0, 7, 4]))      
print(sol.minSum([5]))                 
print(sol.minSum([9, 4]))              
