from bisect import bisect_right

class Solution:
    def countLessEq(self, a, b):
        b.sort()  
        result = []
        for num in a:
            count = bisect_right(b, num)
            result.append(count)
        return result
sol = Solution()
a = [4, 8, 7, 5, 1]
b = [4, 48, 3, 0, 1, 1, 5]
print(sol.countLessEq(a, b))
