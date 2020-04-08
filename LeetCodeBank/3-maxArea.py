#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号11
# 给你 n 个非负整数 a1，a2，...，an，每个数代表坐标中的一个点 (i, ai) 。在坐标内画 n 条垂直线，垂直线 i 的
# 两个端点分别为 (i, ai) 和 (i, 0)。找出其中的两条线，使得它们与 x 轴共同构成的容器可以容纳最多的水。

# 说明：你不能倾斜容器，且 n 的值至少为 2。


# 输入：[1,8,6,2,5,4,8,3,7]
# 输出：49


# 方法一：穷举法， 算出所有的可能, 时间复杂度比较高 O(n*n)
class SolutionV1:

    @staticmethod
    def get_area(a, b, lengt):
        return min(a, b) * lengt

    def maxArea(self, height: 'list') -> int:

        value = 0
        for i in range(len(height)):
            for j in range(i + 1, len(height)):
                value = max(value, (self.get_area(height[i], height[j], j-i)))

        return value


# 方法二： 将范围向中间移动， 只取比当前的高度高的
class Solution:

    def maxArea(self, height: 'list') -> int:

        i = 0
        j = len(height) - 1
        value = 0
        while i < j:
            if height[i] < height[j]:
                value = max(value, (height[i] * (j - i)))
                i += 1
            else:
                value = max(value, (height[j] * (j - i)))
                j -= 1

        return value


if __name__ == '__main__':
    height = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    sol = Solution()
    print(sol.maxArea(height))
