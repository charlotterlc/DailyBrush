#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 84

# 给定 n 个非负整数，用来表示柱状图中各个柱子的高度。每个柱子彼此相邻，且宽度为 1 。
# 求在该柱状图中，能够勾勒出来的矩形的最大面积。


# 图中阴影部分为所能勾勒出的最大矩形面积，其面积为 10 个单位。
#
#  
#
# 示例:
# 输入: [2,1,5,6,2,3]
# 输出: 10


# 暴力法
class SolutionV1:
    def largestRectangleArea(self, heights: list) -> int:

        if not heights:
            return 0

        max_area = 0
        n = len(heights)
        for i in range(n):
            for j in range(i + 1, n):
                value = (j - i + 1) * min(heights[i:j+1])
                max_area = max(value, max_area)

        return max_area


# 使用单调栈的方法   [0,2,1,5,6,2,3,0]
class Solution:
    def largestRectangleArea(self, heights: list) -> int:

        stack = []
        heights = [0] + heights + [0]
        res = 0

        for i in range(len(heights)):

            while stack and heights[stack[-1]] > heights[i]:
                tmp = stack.pop()
                res = max(res, (i - stack[-1] - 1) * heights[tmp])
            stack.append(i)

        return res


if __name__ == '__main__':

    heights = [2,1,5,6,2,3]
    sol = Solution()
    res = sol.largestRectangleArea(heights)
    print(res)