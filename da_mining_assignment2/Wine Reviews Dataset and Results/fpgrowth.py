from collections import defaultdict

# FP Tree Class
class Node:
    def __init__(self, item, count, parent):
        self.item = item
        self.count = count
        self.parent = parent
        self.children = {} # Maps item name to Node's child object
        self.next_node = None
        self.link = None

    def add_child(self, child):
        if child.item not in self.children:
            self.children[child.item] = child

    def increment_count(self, count):
        self.count += count

    def get_nodes_with_item(self, item):
        nodes = []
        if self.item == item:
            nodes.append(self)
        for child in self.children.values():
            nodes.extend(child.get_nodes_with_item(item))
        return nodes

class FPTree:
    def __init__(self):
        self.root = Node("*", 0, None)
        self.header_table = {} # Maps item name to Node object

    def add_transaction(self, transaction):
        current_node = self.root
        for item in transaction:
            # Get child node as node for current item
            child_node = current_node.children.get(item)
            # If child node is None, initialise it
            if child_node is None:
                child_node = Node(item, 0, current_node)
                current_node.children[item] = child_node
                # Connect header table to child node
                if item in self.header_table:
                    last_node = self.header_table[item]
                    while last_node.link is not None:
                        last_node = last_node.link
                    last_node.link = child_node
                else:
                    self.header_table[item] = child_node
            # Increment child node's count
            child_node.increment_count(1)
            # Go 1 level deeper into the tree for next item
            current_node = child_node

    def get_frequent_items(self, min_support):
        """Get individual items which sum of counts reach min_support"""
        frequent_items = {}
        for item in self.header_table:
            support = 0
            node = self.header_table[item]
            while node is not None:
                support += node.count
                node = node.link
            if support >= min_support:
                frequent_items[item] = support
        return frequent_items
    
    def get_nodes_with_item(self, item):
        return self.header_table.get(item, [])
    
# fp-growth
class FP_Growth():
    def __init__(self, transactions, min_support=0.1, min_confidence=0.5):
        self.transactions = transactions
        self.min_support = min_support
        # self.min_confidence = min_confidence
        self.num_transactions = len(transactions)
        self.num_min_support = self.min_support * self.num_transactions
        self.frequent_itemsets = []
        self.ordered_frequent_items = []
        self.ordered_itemsets = []

    def _get_frequent_items(self, transactions=None, order=False):
        if not transactions: transactions = self.transactions
        items_count = defaultdict(int)
        for transaction in transactions:
            for item in transaction:
                items_count[item] += 1

        # Filter frequent 1-itemsets
        frequent_items = [(item, count) for item, count in items_count.items() if count >= self.num_min_support]
        if order:
            # Sort  frequent 1-itemsets by their support
            frequent_items = sorted(frequent_items, key=lambda x: x[1], reverse=True)
        
        frequent_items = [item for item, count in frequent_items]
        return frequent_items

    def _generate_ordered_itemsets(self):
        self.ordered_frequent_items = self._get_frequent_items(order=True)

        is_frequent = defaultdict(int)
        for item in self.ordered_frequent_items:
            is_frequent[item] = 1
        # For each transaction, get items only present in self.ordered_frequent_items
        unordered_itemsets = []
        for transaction in self.transactions:
            items = []
            for item in transaction:
                if is_frequent[item]:
                    items.append(item)
            unordered_itemsets.append(items)
        
        # Sort items by order which they appear in self.ordered_frequent_items
        self.ordered_itemsets = []
        for transaction in unordered_itemsets:
            new_transaction = []
            for item in self.ordered_frequent_items:
                if item in transaction:
                    new_transaction.append(item)
            self.ordered_itemsets.append(new_transaction)

    def _generate_fptree(self, transactions=None):
        if not transactions: transactions = self.transactions.copy()
        self.fptree = FPTree()
        for transaction in self.ordered_itemsets:
            self.fptree.add_transaction(transaction)

    def print_tree(self, node=None, indent_times=0):
        if not node:
            node = self.fptree.root
        indent = "    " * indent_times
        print ("%s%s:%s" % (indent, node.item, node.count))
        for child_key in node.children:
            child = node.children[child_key]
            self.print_tree(child, indent_times + 1)

    def _extract_patterns_from_tree(self, tree):
        """Extract frquent patterns from given fptree"""
        if tree is None: return []

        frequent_patterns = []
        frequent_items = tree.get_frequent_items(self.num_min_support)
        
        for item, count in frequent_items.items():
            # Get base pattern
            base_pattern = [(item, count)]
            # Get conditional patterns
            conditional_pattern_base = self._get_conditional_pattern_base(tree, item)
            # Construct conditional fptree based on conditional patterns
            conditional_tree = self._generate_conditional_fptree(conditional_pattern_base)
            # Recursively mine conditional fptree
            conditional_patterns = self._extract_patterns_from_tree(conditional_tree)
            
            # Add patterns to result
            frequent_patterns.append(base_pattern)
            for pattern in conditional_patterns:
                frequent_patterns.append(base_pattern + pattern)
                
        return frequent_patterns

    def _get_conditional_pattern_base(self, tree, item):
        """ 
        Get patterns that end with the given item 
        Returns a list, where each element of tuples (item, count)
        """
        conditional_pattern_base = []
        node = tree.header_table[item]
        while node is not None:
            pattern = []
            parent = node.parent
            # Traverse from item to root
            while parent.item != "*":
                pattern.append((parent.item, node.count))
                parent = parent.parent
            if pattern: conditional_pattern_base.append(pattern)
            node = node.link
        return conditional_pattern_base 
    
    def _generate_conditional_fptree(self, conditional_pattern_base):
        """Generate fptree given a list of patterns"""
        tree = FPTree()
        for pattern in conditional_pattern_base:
            for _ in range(pattern[0][1]):
                # Only take the items (not counts) for adding a transaction
                transaction = [item[0] for item in pattern]
                tree.add_transaction(transaction)
        return tree#, tree.get_frequent_items(self.num_min_support)

    def run(self, show_tree=False):
        self._generate_ordered_itemsets()
        self._generate_fptree()

        if show_tree:
            print ("FP-Growth Tree:")
            self.print_tree()
            print()

        # Mine frequent itemsets from fptree
        frequent_patterns = self._extract_patterns_from_tree(self.fptree)
        for pattern in frequent_patterns:
            itemset = []
            support = self.num_transactions
            for item, count in pattern:
                itemset.append(item)
                support = min(support, count)
            itemset = frozenset(itemset)
            self.frequent_itemsets.append((itemset, count/self.num_transactions))
        
        return self.frequent_itemsets