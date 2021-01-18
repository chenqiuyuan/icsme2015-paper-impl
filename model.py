
import datetime
from datetime import datetime, timedelta
import pickle as pkl

class TIEModel:
    def __init__(self, word_list, reviewer_list, alpha=0.7, M=100, recommended_count=10, text_splitter=lambda x: x.split(' ')):
        self.reviews = []
        self.word_list = word_list
        self.word_map = self._get_map(word_list)
        self.reviewer_list = reviewer_list
        self.reviewer_map = self._get_map(reviewer_list)
        self.review_count_map = {}
        self.text_models = [dict() for _ in range(len(reviewer_list))]
        self._simularity_cache = {}
        self.text_splitter = text_splitter
        self.M = M
        self.recommended_count = recommended_count
        self.alpha = alpha
    
    @classmethod
    def load(cls, file_path):
        f = open(file_path, 'rb')
        return pkl.load(f)
    
    def update(self, review):
        review = self._transform_review_format(review)
        
        if len(review["textual-content"]) == 0:
            raise Exception("Cannot update.")

        for reviewer_index in review["reviewers"]:
            self.review_count_map[reviewer_index] = self.review_count_map.get(reviewer_index, 0) + 1
            for word_index in review["textual-content"]:
                self.text_models[reviewer_index][word_index] = self.text_models[reviewer_index].get(word_index, 0) + 1
        
        self.reviews.append(review)

    def recommend(self, review):
        review = self._transform_review_format(review)
        L = []
        for j in range(len(self.reviewer_list)):
            c = (1 - self.alpha) * self._get_conf_text(review, j) + self.alpha * self._get_conf_path(review, j)
            L.append((j, c))
        L.sort(key=lambda x: x[1], reverse=True)
        L = list(
            map(lambda x: self.reviewer_list[x],
                map(lambda x: x[0], L)
            )
        )
        return L[:self.recommended_count]

    def save(self, file_path):
        f = open(file_path, 'wb')
        pkl.dump(self, f)
        f.close()
        pass

    def _get_map(self, L):
        d = {}
        for idx, e in enumerate(L):
            d[e] = idx
        return d

    def _calc_simularity(self, rev1, rev2):
        key = str(rev1["id"]) + "-" + str(rev2["id"])
        if key in self._simularity_cache:
            return self._simularity_cache[key]
        changed_files1 = rev1["changed-files"][:500]
        changed_files2 = rev2["changed-files"][:500]
        if len(changed_files1) == 0 or len(changed_files2) == 0:
            return 0
        sum_score = 0
        for f1 in changed_files1:
            s1 = set(f1.split('/'))
            for f2 in changed_files2:
                s2 = set(f2.split('/'))
                sum_score += (len(s1 & s2)) / max(len(s1), len(s2))
        ret = sum_score / (len(changed_files1) * len(changed_files2) + 1)
        self._simularity_cache[key] = ret
        return ret
    
    def _get_conf_path(self, review, reviewer_index):
        s = 0
        end_time = review["uploaded-time"]
        start_time = (datetime.fromtimestamp(end_time) - timedelta(days=self.M)).timestamp()

        start_idx = self._review_history_start_index(start_time)
        end_idx = self._review_history_end_index(end_time)
        if start_idx == -1 or end_idx == -1:
            return 0
        for i in range(start_idx, end_idx):
            old_rev = self.reviews[i]
            c = self._calc_simularity(old_rev, review)
            for index in old_rev["reviewers"]:
                if index == reviewer_index:
                    s += c
                    break
        return s
    
    def _get_conf_text(self, review, reviewer_index):
        product = 1
        s = 0
        for k, v in self.text_models[reviewer_index].items():
            s += v
        for word_index in review["textual-content"]:
            p = self.text_models[reviewer_index].get(word_index, 1e-9) / (s + 1)
            product *= p
        return self.review_count_map.get(reviewer_index, 0) / len(self.reviews) * product

    def _transform_review_format(self, review):
        word_indices = list(map(lambda x: self.word_map[x],
            filter(lambda x: x in self.word_map.keys(),
                self.text_splitter(review["textual-content"])
            )
        ))
        reviewer_indices = [self.reviewer_map[_reviewer["id"]] for _reviewer in review["reviewers"]]
        return {
            "textual-content": word_indices,
            "reviewers": reviewer_indices,
            "id": review["id"],
            "uploaded-time": int(datetime.strptime(review["uploaded-time"], "%Y-%m-%d %H:%M:%S").timestamp()),
            "changed-files": review["changed-files"]
        }

    def _review_history_start_index(self, t):
        i = 0
        j = len(self.reviews) - 1
        while i < j:
            mid = (i + j) // 2
            if self.reviews[mid]["uploaded-time"] <= t:
                i = mid + 1
            else:
                j = mid
            
        if self.reviews[i]["uploaded-time"] > t:
            return i
        else:
            return -1
    
    def _review_history_end_index(self, t):
        i = 0
        j = len(self.reviews) - 1
        while i < j:
            mid = (i + j + 1) // 2
            if self.reviews[mid]["uploaded-time"] < t:
                i = mid
            else:
                j = mid - 1

        if self.reviews[i]["uploaded-time"] < t:
            return i
        else:
            return -1


