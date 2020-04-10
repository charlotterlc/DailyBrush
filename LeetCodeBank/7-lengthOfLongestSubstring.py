#! /usr/bin/env python
# coding: utf-8

# 不重复字符串
# 给定一个字符串，请你找出其中不含有重复字符的 最长子串 的长度。
# 示例 1:
# 输入: "abcabcbb"
# 输出: 3
# 解释: 因为无重复字符的最长子串是 "abc"，所以其长度为 3。

# 示例 2:
# 输入: "bbbbb"
# 输出: 1
# 解释: 因为无重复字符的最长子串是 "b"，所以其长度为 1。

# 示例 3:
# 输入: "pwwkew"
# 输出: 3
# 解释: 因为无重复字符的最长子串是 "wke"，所以其长度为 3。
# 请注意，你的答案必须是 子串 的长度，"pwke" 是一个子序列，不是子串。


def lengthOfLongestSubstring(s: 'str') -> 'int':
    # 思路：遍历数据， 判断队列里是否存在该元素， 存在就删除队列的最左元素，直至不存在为止， 获取当前的长度进行比较

    if not s: return 0
    from collections import deque
    _stack = deque()
    max_value = 0
    for j in s:
        while j in _stack:
            # 删除最先加入的元素（字符串最左边的）
            _stack.popleft()

        _stack.append(j)
        max_value = max(max_value, len(_stack))

    return max_value


if __name__ == '__main__':
    s = "pwwkew"
    print(lengthOfLongestSubstring(s))