#! /usr/bin/env python
# coding: utf-8

# 运用你所掌握的数据结构，设计和实现一个  LRU (最近最少使用) 缓存机制。它应该支持以下操作： 获取数据 get 和 写入数据 put 。

# 获取数据 get(key) - 如果密钥 (key) 存在于缓存中，则获取密钥的值（总是正数），否则返回 -1。
# 写入数据 put(key, value) - 如果密钥已经存在，则变更其数据值；如果密钥不存在，则插入该组「密钥/数据值」。当缓存容量达到上限时，
# 它应该在写入新数据之前删除最久未使用的数据值，从而为新的数据值留出空间。


# 思路
# 1.使用hash map在时间复杂度O(1)的查找key值对应的val；
# 2.同时要在O(1)时间内找到对应链表的节点，完成在原链表中的移除并且添加到链表头部；
# 因此设计的时候应该是 unordered_map<key, list::iterator>
# 3.在这个缓冲区满的时候，找到list对应的节点进行删除，同时还需要删除原hash map中的内容，
# 所以需要从list中需要存储key值，这样才能返回hash map中去删除元素
# list<pair<key, val>> unordered_map<key, list<pair<key, val>>::iterator>


# 简单版本， 使用的列表做为缓存区
class LRUCacheV1:

    def __init__(self, capacity: int):
        # 将数据存储在hash_map中
        self.map = {}

        # 数据的长度
        self.length = capacity

        # 设置缓存区
        self.stack = []

    def get(self, key: int) -> int:
        value = self.map.get(key)
        if not value:
            return -1

        self.stack.remove(key)
        self.stack.append(key)
        return value

    def put(self, key: int, value: int) -> None:

        # 判断key是否存在
        if key in self.map:
            self.map[key] = value
            # 将key移动到stack的头部
            self.stack.remove(key)
            self.stack.append(key)
            return

        # 判断长度是否够
        if len(self.stack) >= self.length:
            # 删除最后一个
            last_key = self.stack[0]
            del self.map[last_key]
            self.stack.remove(last_key)

        self.map[key] = value
        self.stack.append(key)

        return


# 进阶版， 使用链表的结构作为缓存区
# 创建双向链表
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:

    def __init__(self, capacity: int):
        # 构建首尾节点, 使之相连
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

        self.lookup = dict()  # 字典中存储为key 和对应的Node
        self.max_len = capacity

    def get(self, key: int) -> int:
        if key in self.lookup:
            node = self.lookup[key]
            self.remove(node)
            self.add(node)
            return node.value
        else:
            return -1

    def put(self, key: int, value: int) -> None:
        if key in self.lookup:
            self.remove(self.lookup[key])
        if len(self.lookup) == self.max_len:
            # 把表头位置节点删除(说明最近的数据值)
            self.remove(self.head.next)
        self.add(Node(key, value))

    # 删除链表节点
    def remove(self, node):
        del self.lookup[node.key]
        node.prev.next = node.next
        node.next.prev = node.prev

    # 加在链表尾
    def add(self, node):
        self.lookup[node.key] = node
        pre_tail = self.tail.prev
        node.next = self.tail
        self.tail.prev = node
        pre_tail.next = node
        node.prev = pre_tail


if __name__ == '__main__':
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    print(cache.get(1))
    cache.put(3, 3)
    print(cache.get(2))
    cache.put(4, 4)
    print('1',cache.get(1))
    print('3',cache.get(3))
    print('4',cache.get(4))


