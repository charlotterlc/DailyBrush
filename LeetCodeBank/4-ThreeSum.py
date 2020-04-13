#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 15

# 给你一个包含 n 个整数的数组 nums，判断 nums 中是否存在三个元素 a，b，c ，使得 a + b + c = 0 ？
# 请你找出所有满足条件且不重复的三元组。
# 注意：答案中不可以包含重复的三元组。

# 示例： 给定数组 nums = [-1, 0, 1, 2, -1, -4]
# 满足要求的三元组集合为：
# [
#   [-1, 0, 1],
#   [-1, -1, 2]
# ]

# 暴力法  时间复杂度：O(n^3)
class SolutionV1:

    def threeSum(self, nums: 'list') -> 'list':

        l = []
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                for k in range(j + 1, len(nums)):
                    if nums[i] + nums[j] + nums[k] == 0:
                        res = [nums[i], nums[j], nums[k]]
                        res.sort()
                        if res not in l:
                            l.append(res)

        return l


# 双指针的方法   时间复杂度：O(n^2)
class Solution:

    def threeSum(self, nums: 'list') -> 'list':

        n = len(nums)
        res = []
        if n < 3:
            return res

        nums.sort()  # 进行排序
        for i in range(n):

            # 最小值大于0时， 不需要再遍历， 直接退出
            if nums[i] > 0:
                return res

            # 排序过的数组， 相同元素时， 直接跳过
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            L = i + 1   # 左指针为i 的后一位
            R = n - 1   # 右指针为数组的最后一位

            while L < R:
                if nums[i] + nums[L] + nums[R] == 0:
                    res.append([nums[i], nums[L], nums[R]])

                    # 指针推进时， 如果数值相同， 则跳过
                    while L < R and nums[L] == nums[L + 1]:
                        L += 1

                    # 指针推进时， 如果数值相同， 则跳过
                    while L < R and nums[R] == nums[R - 1]:
                        R -= 1

                    L += 1
                    R -= 1
                elif nums[i] + nums[L] + nums[R] > 0:
                    # 大于0时， 右指针偏移
                    R -= 1
                else:
                    L += 1

        return res


if __name__ == '__main__':
    nums = [-1, 0, 1, 2, -1, -4]

    sol = Solution()
    print(sol.threeSum(nums))
