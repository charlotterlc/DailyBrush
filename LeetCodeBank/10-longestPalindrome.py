#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 5


# 给定一个字符串 s，找到 s 中最长的回文子串。你可以假设 s 的最大长度为 1000。

# 示例 1：
# 输入: "babad"
# 输出: "bab"
# 注意: "aba" 也是一个有效答案。

# 示例 2：
# 输入: "cbbd"
# 输出: "bb"


# 暴力法1、获取所有的边界、进行判断
class SolutionV1:
    def longestPalindrome(self, s: str) -> str:

        if len(s) <= 1:
            return s

        max_len = 0
        res = ""
        for i in range(len(s)):
            for j in range(i+1, len(s)+1):
                new_s = s[i:j]
                if new_s == new_s[::-1]:
                    res = new_s if len(new_s) >= max_len else res
                    max_len = max(len(new_s), max_len)

        return res


# 暴力法2、以字符串为中心，错误版
class SolutionV2:
    def longestPalindrome(self, s: str) -> str:

        len_s = len(s)

        if len_s <= 1:
            return s
        if len_s == 2:
            return s[0]

        max_len = 0
        res = ""

        for i in range(len_s):
            R = i + 1
            L = i - 1

            # 当中心为奇数时， 没有考虑当为偶数时的状况
            while L >= 0 and R < len_s:
                if s[L] == s[R]:
                    # 判断当前的长度
                    res = s[L:R+1] if R - L + 1 >= max_len else res
                    max_len = max(max_len, R - L + 1)
                    L -= 1
                    R += 1
                else:
                    break


        return res


# 暴力法2、以字符串为中心
class SolutionV3:
    def extend(self, i, index, n, s):
        while i >= 1 and index < n - 1:
            if s[i - 1] == s[index + 1]:
                i -= 1
                index += 1
            else:
                break
        return i, index

    def longestPalindrome(self, s: str) -> str:
        n = len(s)
        i = 0
        max = 0
        start = 0
        end = 0
        while i < n:
            index = i
            while index < n - 1 and s[index] == s[index + 1]:
                index += 1
            a, b = self.extend(i, index, n, s)
            if b - a + 1 > max:
                max = b - a + 1
                start = a
                end = b
            i = index + 1
        return s[start:end + 1]

    def longestPalindrome2(self, s: str) -> str:
        def expand(l, r):
            while 0 <= l and r < n and s[l] == s[r]:
                l -= 1
                r += 1
            return r - l - 1

        if not s or len(s) == 1:
            return s
        n = len(s)
        start = 0
        end = 0
        for i in range(n):
            len1 = expand(i, i)
            len2 = expand(i, i + 1)
            len_long = max(len1, len2)
            if (len_long > end - start):
                start = i - (len_long - 1) // 2
                end = i + (len_long) // 2
        return s[start:end + 1]


class SolutionV4:
    def longestPalindrome(self, s: str) -> str:
        # 中心扩散方法
        if not s or len(s) == 1:
            return s

        def get_len_num(l, r):
            while l >= 0 and r < n and s[l] == s[r]:
                l -= 1
                r += 1
            return r - l - 1

        n = len(s)
        start = 0
        end = 0
        max_len = 0

        for i in range(n - 1):
            len_j = get_len_num(i, i)
            len_o = get_len_num(i, i + 1)

            len_i = max(len_j, len_o)
            if len_i > max_len:
                start = i - (len_i - 1) // 2
                end = i + (len_i) // 2
                max_len = len_i
        return s[start:end + 1]


    def longestPalindrome2(self, s: str) -> str:

        if not s or len(s) == 1:
            return s
        n = len(s)
        i = 0
        start = 0
        end = 0
        max_len = 0

        def get_start_end(start, end):
            while start >= 1 and end < n - 1 and s[start - 1] == s[end + 1]:
                start -= 1
                end += 1

            return start, end

        while i < n:
            index = i

            while index < n - 1 and s[index] == s[index + 1]:
                index += 1

            l, r = get_start_end(i, index)
            if max_len < r - l + 1:
                max_len = r - l + 1
                start = l
                end = r

            i = index + 1

        return s[start:end+1]



if __name__ == '__main__':
    s = "aaa"
    sol = SolutionV4()
    print(sol.longestPalindrome2(s))