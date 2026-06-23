class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.original_names = []  # List of original filenames matching this prefix node

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, original_name):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            if original_name not in node.original_names:
                node.original_names.append(original_name)
        node.is_end_of_word = True

    def search_prefix(self, prefix):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return node.original_names

class MaxHeap:
    def __init__(self):
        self.heap = []

    def parent(self, i):
        return (i - 1) // 2

    def left_child(self, i):
        return 2 * i + 1

    def right_child(self, i):
        return 2 * i + 2

    def insert(self, item):
        # item is (access_count, file_obj)
        self.heap.append(item)
        self.heapify_up(len(self.heap) - 1)

    def heapify_up(self, i):
        while i > 0 and self.heap[i][0] > self.heap[self.parent(i)][0]:
            parent_idx = self.parent(i)
            self.heap[i], self.heap[parent_idx] = self.heap[parent_idx], self.heap[i]
            i = parent_idx

    def extract_max(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        max_item = self.heap[0]
        self.heap[0] = self.heap.pop()
        self.heapify_down(0)
        return max_item

    def heapify_down(self, i):
        max_idx = i
        left = self.left_child(i)
        right = self.right_child(i)

        if left < len(self.heap) and self.heap[left][0] > self.heap[max_idx][0]:
            max_idx = left

        if right < len(self.heap) and self.heap[right][0] > self.heap[max_idx][0]:
            max_idx = right

        if i != max_idx:
            self.heap[i], self.heap[max_idx] = self.heap[max_idx], self.heap[i]
            self.heapify_down(max_idx)

    def size(self):
        return len(self.heap)
