#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 42


# 给定 n 个非负整数表示每个宽度为 1 的柱子的高度图，计算按此排列的柱子，下雨之后能接多少雨水。

# 输入: [0,1,0,2,1,0,1,3,2,1,2,1]
# 输出: 6


# 使用单调递减栈的方式
class Solution:
    def trap(self, height: list) -> int:

        stack = []
        sum_trap = 0
        if len(height) < 3: return 0

        for i in range(len(height)):

            while stack and height[i] > height[stack[-1]]:
                value = stack.pop()
                if not stack:
                    break
                sum_trap += min((height[stack[-1]] - height[value]), (height[i] - height[value])) * (i - stack[-1] - 1)
            stack.append(i)

        return sum_trap


if __name__ == '__main__':
    height = [4,2,3]
    sol = Solution()
    print(sol.trap(height))
