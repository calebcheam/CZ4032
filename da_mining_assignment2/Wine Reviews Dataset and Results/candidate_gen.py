from collections import defaultdict
import itertools

# candidate generation
class CandidateGen:
    def __init__(self, transactions, min_support=0.1, min_confidence=0.5):
        self.transactions = transactions
        self.min_support = min_support
        # self.min_confidence = min_confidence
        self.itemsets = defaultdict(int)
        self.hash_buckets = defaultdict(int)
        self.num_transactions = len(transactions)
        self.frequent_itemsets = []

    def _generate_candidate_itemsets(self, prev_frequent_itemsets, k):
        candidates = set()
        for itemset1 in prev_frequent_itemsets:
            for itemset2 in prev_frequent_itemsets:
                new_candidate = itemset1.union(itemset2)
                if len(new_candidate) == k:
                    all_subsets_are_frequent = all([frozenset(subset) in prev_frequent_itemsets for subset in itertools.combinations(new_candidate, k-1)])
                    if all_subsets_are_frequent:
                        candidates.add(new_candidate)
        return candidates

    def _apply_pcy(self):
        #first pass: count the pairs in each bucket
        for transaction in self.transactions:
            for pair in itertools.combinations(sorted(transaction), 2):  # Sorting ensures consistent order
                bucket = hash(pair) % 10000
                self.hash_buckets[bucket] += 1

        #determine the frequent buckets
        bucket_threshold = self.min_support * self.num_transactions  # Using raw counts instead of ratios for bucket threshold
        self.hash_buckets = {bucket for bucket, count in self.hash_buckets.items() if count >= bucket_threshold}

    def run(self):
        self._apply_pcy() # pcy in first pass
        for transaction in self.transactions:
            for item in transaction:
                self.itemsets[frozenset([item])] += 1

        #filter frequent 1-itemsets
        self.frequent_itemsets = [(itemset, count / self.num_transactions) for itemset, count in self.itemsets.items() if count / self.num_transactions >= self.min_support]

        k = 2
        while True:
            candidates = self._generate_candidate_itemsets([item[0] for item in self.frequent_itemsets], k) # generate candidates
            if k == 2:  #pcy only applicable for pairs in the second pass
                candidates = [candidate for candidate in candidates if hash(tuple(sorted(candidate))) % 10000 in self.hash_buckets]
            candidate_counts = defaultdict(int)
            for transaction in self.transactions:
                for candidate in candidates:
                    if candidate.issubset(transaction):
                        candidate_counts[candidate] += 1

            #filter frequent itemsets
            new_frequent_itemsets = [(itemset, count / self.num_transactions) for itemset, count in candidate_counts.items() if count / self.num_transactions >= self.min_support]

            if not new_frequent_itemsets:
                break

            self.frequent_itemsets.extend(new_frequent_itemsets)
            k += 1

        return self.frequent_itemsets