#! /usr/bin/env python
# coding: utf-8


# LeetCode 题号 20
# 给定一个只包括 '('，')'，'{'，'}'，'['，']' 的字符串，判断字符串是否有效。
# 有效字符串需满足：
# 左括号必须用相同类型的右括号闭合。
# 左括号必须以正确的顺序闭合。
# 注意空字符串可被认为是有效字符串。

# 输入: "()[]{}"
# 输出: true


def isValid(s: str) -> bool:
    # 把字符串当成一个栈，前进后出
    parenthes_map = {")": "(", "]": "[", "}": "{"}
    _stack = []

    for parenthe in s:
        if parenthe in parenthes_map.values():
            _stack.append(parenthe)

        if parenthe in parenthes_map:
            _map_par = parenthes_map.get(parenthe)
            if _stack and _stack[-1] == _map_par:
                _stack.pop()
            else:
                return False

    return True if not _stack else False


if __name__ == '__main__':
    print(isValid("({][])"))