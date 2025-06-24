class Solution:
    def maxSubseq(self, s: str, k: int) -> str:
        stack = []
        to_remove = k

        for c in s:
            while stack and to_remove > 0 and stack[-1] < c:
                stack.pop()
                to_remove -= 1
            stack.append(c)
        while to_remove > 0:
            stack.pop()
            to_remove -= 1
        return ''.join(stack)
s = "zrptllivngoi"
k = 11
print(Solution().maxSubseq(s, k))  
