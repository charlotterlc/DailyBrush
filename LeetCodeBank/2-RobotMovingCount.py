#! /usr/bin/env python
# coding: utf-8

# 地上有一个m行n列的方格，从坐标 [0,0] 到坐标 [m-1,n-1] 。一个机器人从坐标 [0, 0] 的格子开始移动，它每次可以向左、右、
# 上、下移动一格（不能移动到方格外），也不能进入行坐标和列坐标的数位之和大于k的格子。例如，当k为18时，机器人能够进入
# 方格 [35, 37] ，因为3+5+3+7=18。但它不能进入方格 [35, 38]，因为3+5+3+8=19。请问该机器人能够到达多少个格子？


# 输入：m = 2, n = 3, k = 1
# 输出：3

# 1 <= n,m <= 100
# 0 <= k <= 20

# 错误的版本， 遍历了二维数组，获取所有能走到的格子， 应该是每走一格，然选择下一个走法，计算能走多少格
class SolutionV1:

    def movingCount(self, m: int, n: int, k: int) -> int:
        number = 0
        # 1、想到的首先进行遍历
        for line in range(m):
            for column in range(n):

                # 现在的坐标为[line, column], 获取位数之和进行判断
                d_line = self.get_digit_num(line)
                d_column = self.get_digit_num(column)

                if d_line + d_column > k:
                    break
                number += 1
        return number

    # 获取对应的位数
    @staticmethod
    def get_digit_num(value):

        # 十位数的数值
        num1 = value // 10
        num2 = value % 10
        return num1 + num2


# 广度优先算法
class Solution:

    @staticmethod
    def add_coor(a, b):
        ans = 0
        while a != 0:
            ans += a % 10
            a //= 10
        while b != 0:
            ans += b % 10
            b //= 10
        return ans

    def movingCount(self, m: int, n: int, k: int) -> int:
        # 计算位数的和

        from collections import deque
        mat = [[0 for _ in range(n)] for _ in range(m)]  # 先创建 m x n 的矩阵并都设为 0
        mat[0][0] = 1  # 将初始位置设为1，代表已经访问过
        temp = deque()  # 用一个队列存储即将扩展的点的坐标
        temp.append([0, 0])
        res = 0
        # BFS经典模板
        while temp:
            temp_point = temp.popleft()
            res += 1
            x, y = temp_point
            for x_bias, y_bias in [[0, 1], [0, -1], [1, 0], [-1, 0]]:
                new_x = x + x_bias
                new_y = y + y_bias
                if new_x < 0 or new_x > m - 1 or new_y < 0 or new_y > n - 1 or self.add_coor(new_x, new_y) > k or mat[new_x][
                    new_y] == 1:
                    continue
                mat[new_x][new_y] = 1
                temp.append([new_x, new_y])

        return res




if __name__ == '__main__':
    solut = Solution()
    print(solut.movingCount(m = 3, n = 2, k = 2))