def two_sum_sorted(nums, target):
    left = 0
    right = len(nums) - 1

    while left < right:
        current_sum = nums[left] + nums[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return []
print("Enter the list of numbers separated by space:")
nums = list(map(int, input().split()))
nums = sorted(nums) 
target = int(input("Enter the target: "))
result = two_sum_sorted(nums, target)
print("Indices in sorted array:", result if result else "No pair found.")
