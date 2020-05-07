#! /usr/bin/env python
# coding: utf-8
from typing import List

# 一、
# 设计一个支持 push ，pop ，top 操作，并能在常数时间内检索到最小元素的栈。
# push(x) —— 将元素 x 推入栈中。
# pop() —— 删除栈顶的元素。
# top() —— 获取栈顶元素。
# getMin() —— 检索栈中的最小元素。

# 示例:
# MinStack minStack = new MinStack();
# minStack.push(-2);
# minStack.push(0);
# minStack.push(-3);
# minStack.getMin();   --> 返回 -3.
# minStack.pop();
# minStack.top();      --> 返回 0.
# minStack.getMin();   --> 返回 -2.


# 使用辅助栈， 如果有新的最小值则加入辅助栈
class MinStack:

    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, x: int) -> None:
        self.stack.append(x)
        if not self.min_stack or x <= self.min_stack[-1]:
            self.min_stack.append(x)

    # 删除元素时， 判断是否为最小元素， 是的话就一起删除辅助栈的栈顶元素
    def pop(self) -> None:
        if self.stack.pop() == self.min_stack[-1]:
            self.min_stack.pop()

    def top(self) -> int:
        if self.stack:
            return self.stack[-1]

    def getMin(self) -> int:
        if self.min_stack:
            return self.min_stack[-1]


# 计算最大面积
class Solution:
    def largestRectangleArea(self, heights: list) -> int:
        # 使用单调栈的方式计算

        stack = []
        max_area = 0
        heights = [0] + heights + [0]
        for i in range(len(heights)):
            while stack and heights[i] < heights[stack[-1]]:
                # 计算最大的面积
                h_value = stack.pop()
                area = heights[h_value] * (i - stack[-1] - 1)
                max_area = max(max_area, area)
            stack.append(i)

        return max_area


# 242. 有效的字母异位词 字母异位词指字母相同，但排列不同的字符串。
# 给定两个字符串 s 和 t ，编写一个函数来判断 t 是否是 s 的字母异位词。
# 示例 1:
# 输入: s = "anagram", t = "nagaram"
# 输出: true
class Solution:
    def isAnagramV1(self, s: str, t: str) -> bool:
        # 暴力法， 进行排序， 然后判断是否相同
        s1 = sorted(s)
        t1 = sorted(t)
        return s1 == t1

    def isAnagram(self, s: str, t: str) -> bool:
        # 使用集合， 然后判断count是否相等
        s1 = set(s)

        if len(s) != len(t):
            return False

        for i in s1:
            if s.count(i) != t.count(i):
                return False
        return True


# 49. 字母异位词分组
# 给定一个字符串数组，将字母异位词组合在一起。字母异位词指字母相同，但排列不同的字符串。

# 示例:
# 输入: ["eat", "tea", "tan", "ate", "nat", "bat"]
# 输出:
# [
#   ["ate","eat","tea"],
#   ["nat","tan"],
#   ["bat"]
# ]

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        res = {}
        for word in strs:
            key = "".join(sorted(word))
            if key in res:
                res[key].append(word)
            else:
                res[key] = [word]
        return list(res.values())





if __name__ == '__main__':
    strs =  ["eat", "tea", "tan", "ate", "nat", "bat"]
    sol = Solution()
    print(sol.groupAnagrams(strs))
