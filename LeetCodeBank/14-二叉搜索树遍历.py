#! /usr/bin/env python
# coding: utf-8

# LeetCode 题号 94

# 给定一个二叉树，返回它的中序 遍历。
#
# 示例:
#
# 输入: [1,null,2,3]
#    1
#     \
#      2
#     /
#    3
#
# 输出: [1,3,2]
import weakref
from typing import List

class TreeNode:
    def __init__(self, item, less=None, more=None, parent=None):
        self.item = item 			# 代表当前节点
        self.less = less			# 小于当前节点的分支
        self.more = more			# 大于当前节点的分支
        if parent is not None:
            self.parent = parent

    @property
    def parent(self):
        return self.parent_ref()

    @parent.setter
    def parent(self,value):
        # 使用弱引用，方便内存回收。
        self.parent_ref = weakref.ref(value)

    def __repr__(self):
        return ("TreeNode({item!r},{less!r},{more!r})".format(**self.__dict__))

    def find(self, item):
        if self.item is None:
            # 为None时代表当前为根节点，所以向more分支递归搜索。
            if self.more:
                return self.more.find(item)
        elif self.item == item:
            # 相等时为找到了节点
            return self
        elif self.item > item and self.less:
            # 如果当前节点大于目标对象，并且小于分支存在的话，那么向less分支递归搜索
            return self.less.find(item)
        elif self.item < item and self.more:
            # 如果当前节点小于目标对象，并且大于分支存在的话，那么向more分支递归搜索
            return self.more.find(item)
        # 如果以上判断都不符合条件，那么搜索的元素不存在
        raise KeyError

    def __iter__(self):
        # 如果当前节点小于分支存在，那么遍历并返回。
        # 使用yield可以节省开销。
        if self.less:
            for item in iter(self.less):
                yield item
        # 返回当前节点
        yield self.item
        # 如果当前节点大于分支存在，那么遍历并返回。
        if self.more:
            for item in iter(self.more):
                yield item

    def add(self, item):
        # 为None时代表当前为根节点，向more分支添加节点
        if self.item is None:
            if self.more:
                self.more.add(item)
            else:
                self.more = TreeNode(item, parent=self)
        # 如果当前节点大于等于添加节点，那么向less分支添加节点
        elif self.item >= item:
            if self.less:
                self.less.add(item)
            else:
                self.less = TreeNode(item, parent=self)
        # 如果当前节点小于添加节点，那么向more节点
        elif self.item < item:
            if self.more:
                self.more.add(item)
            else:
                self.more = TreeNode(item, parent=self)

    def remove(self, item):
        # 如果当前节点为None或者目标节点大于当前节点，那么向more分支递归
        if self.item is None or item> self.item:
            if self.more:
                self.more.remove(item)
            else:
                raise KeyError
        # 如果目标节点小于当前节点，那么向less分支递归
        elif item < self.item:
            if self.less:
                self.less.remove(item)
            else:
                raise KeyError
        else: # self.item == item 即找到了目标元素
            # 如果当前节点具有less分支和more分支
            if self.less and self.more:
                successor = self.more._least() 	# 递归找当前节点more分支中的最小节点
                self.item = successor.item  	# 并将当前节点的值设置为最小节点的值
                successor.remove(successor.item) # 继续递归寻找合适的_replace操作
            # 如果当前节点仅有less分支
            elif self.less:
                self._replace(self.less)
            elif self.more:
                self._replace(self.more)
            # 叶子节点
            else:
                self._replace(None)

    def _least(self):
        # 递归搜索最小的节点
        if self.less is None:
            return self
        return self.less._least()

    def _replace(self,new=None):
        # 如果当前节点存在父节点
        if self.parent:
            # 如果当前节点在父节点的小于分支，那么将小于分支设置为new值
            if self == self.parent.less:
                self.parent.less = new
            # 如果当前节点在父节点的大于分支，那么将大于分支设置为new值
            else:
                self.parent.more = new
        # 如果指定了父节点，那么替换父节点指向
        if new is not None:
            new.parent = self.parent


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


class Solution:
    def inorderTraversal(self, root: TreeNode) -> List[int]:
        pass


if __name__ == '__main__':
    pass