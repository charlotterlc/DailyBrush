#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 2


# 给出两个 非空 的链表用来表示两个非负的整数。其中，它们各自的位数是按照 逆序 的方式存储的，
# 并且它们的每个节点只能存储 一位 数字。
# 如果，我们将这两个数相加起来，则会返回一个新的链表来表示它们的和。
# 您可以假设除了数字 0 之外，这两个数都不会以 0 开头。
# 示例：
# 输入：(2 -> 4 -> 3) + (5 -> 6 -> 4)
# 输出：7 -> 0 -> 8
# 原因：342 + 465 = 807


# Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None


class Solution:
    def addTwoNumbers(self, l1: ListNode, l2: ListNode) -> ListNode:
        num1 = num2 = 0
        i = 0
        current = l1
        while current is not None:
            num1 += current.val * (10 ** i)
            current = current.next
            i += 1
        i = 0
        current = l2
        while current is not None:
            num2 += current.val * (10 ** i)
            current = current.next
            i += 1
        the_sum = num1 + num2
        sum_list = list(str(the_sum))
        resList = ListNode(int(sum_list.pop()))
        position = resList
        for k in range(len(sum_list)):
            temp = ListNode(int(sum_list.pop()))
            position.next = temp
            position = position.next
        return resList


if __name__ == '__main__':

    sol = Solution()
    print(sol.addTwoNumbers())