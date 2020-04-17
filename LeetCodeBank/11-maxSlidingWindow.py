#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 239

# 给定一个数组 nums，有一个大小为 k 的滑动窗口从数组的最左侧移动到数组的最右侧。你只可以看到在滑动窗口内的 k 个数字。
# 滑动窗口每次只向右移动一位。
# 返回滑动窗口中的最大值。

# 示例:
# 输入: nums = [1,3,-1,-3,5,3,6,7], 和 k = 3
# 输出: [3,3,5,5,6,7]
# 解释:
#   滑动窗口的位置                最大值
# ---------------               -----
# [1  3  -1] -3  5  3  6  7       3
#  1 [3  -1  -3] 5  3  6  7       3
#  1  3 [-1  -3  5] 3  6  7       5
#  1  3  -1 [-3  5  3] 6  7       5
#  1  3  -1  -3 [5  3  6] 7       6
#  1  3  -1  -3  5 [3  6  7]      7

from typing import List
from collections import deque


class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        from collections import deque
        if not nums:
            return None

        if len(nums) < k:
            return [max(nums)]

        mydeque = deque(nums[0:k], maxlen=k)
        res = [max(mydeque)]

        for i in range(k, len(nums)):
            mydeque.append(nums[i])
            res.append(max(mydeque))

        return res




if __name__ == '__main__':
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    k = 3
    sol = Solution()
    print(sol.maxSlidingWindow(nums, k))
