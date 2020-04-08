#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 15

# 给你一个包含 n 个整数的数组 nums，判断 nums 中是否存在三个元素 a，b，c ，使得 a + b + c = 0 ？
# 请你找出所有满足条件且不重复的三元组。
# 注意：答案中不可以包含重复的三元组。

# 示例： 给定数组 nums = [-1, 0, 1, 2, -1, -4]，
# 满足要求的三元组集合为：
# [
#   [-1, 0, 1],
#   [-1, -1, 2]
# ]

# 1、穷举试试
class Solution:

    def threeSum(self, nums: 'list') -> 'list':

        l = []
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                for k in range(j+1, len(nums)):
                    if i + j + k == 0:
                        l.append([nums[i], nums[j], nums[k]])

        return l


if __name__ == '__main__':
    nums = [-1, 0, 1, 2, -1, -4]

    sol = Solution()
    print(sol.threeSum(nums))
