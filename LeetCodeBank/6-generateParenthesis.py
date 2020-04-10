#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 22

# 22. 括号生成
# 数字 n 代表生成括号的对数，请你设计一个函数，用于能够生成所有可能的并且 有效的 括号组合。

# 输入：n = 3
# 输出：[
#        "((()))",
#        "(()())",
#        "(())()",
#        "()(())",
#        "()()()"
#      ]


# 当我们清楚所有 i<n 时括号的可能生成排列后，对与 i=n 的情况，我们考虑整个括号排列中最左边的括号。
# 它一定是一个左括号，那么它可以和它对应的右括号组成一组完整的括号 "( )"，我们认为这一组是相比 n-1 增加进来的括号。
# 那么，剩下 n-1 组括号有可能在哪呢？
# 【这里是重点，请着重理解】
# 剩下的括号要么在这一组新增的括号内部，要么在这一组新增括号的外部（右侧）。
# 既然知道了 i<n 的情况，那我们就可以对所有情况进行遍历：
# "(" + 【i=p时所有括号的排列组合】 + ")" + 【i=q时所有括号的排列组合】
# 其中 p + q = n-1，且 p q 均为非负整数。
# 事实上，当上述 p 从 0 取到 n-1，q 从 n-1 取到 0 后，所有情况就遍历完了。
# 注：上述遍历是没有重复情况出现的，即当 (p1,q1)≠(p2,q2) 时，按上述方式取的括号组合一定不同。


class Solution:
    def generateParenthesis(self, n: int) -> list:
        if n == 0:
            return []
        total_l = []
        total_l.append([None])  # 0组括号时记为None
        total_l.append(["()"])  # 1组括号只有一种情况
        for i in range(2, n + 1):  # 开始计算i组括号时的括号组合
            l = []
            for j in range(i):  # 开始遍历 p q ，其中p+q=i-1 , j 作为索引
                now_list1 = total_l[j]  # p = j 时的括号组合情况
                now_list2 = total_l[i - 1 - j]  # q = (i-1) - j 时的括号组合情况
                for k1 in now_list1:
                    for k2 in now_list2:
                        if k1 == None:
                            k1 = ""
                        if k2 == None:
                            k2 = ""
                        el = "(" + k1 + ")" + k2
                        l.append(el)  # 把所有可能的情况添加到 l 中
            total_l.append(l)  # l这个list就是i组括号的所有情况，添加到total_l中，继续求解i=i+1的情况
        return total_l[n]


if __name__ == '__main__':
    pass
