class Solution:
    def majorityElement(self, arr):
        maj = None
        count = 0
        for num in arr:
            if count == 0:
                maj = num
                count = 1
            elif num == maj:
                count += 1
            else:
                count -= 1

        if arr.count(maj) > len(arr) // 2:
            return maj
        else:
            return -1
sol = Solution()
print(sol.majorityElement([3, 1, 3, 3, 2]))  

