import re
import json

def calc_simularity(rev1, rev2):
    changed_files1 = rev1["changed-files"]
    changed_files2 = rev2["changed-files"]
    sum_score = 0
    for f1 in changed_files1:
        s1 = set(f1.split('/'))
        for f2 in changed_files2:
            s2 = set(f2.split('/'))
            sum_score += len(s1 & s2) / max(len(s1), len(s2))

    return sum_score / (len(changed_files1) * len(changed_files2) + 1)

def get_all_reviewers(reviews):
    reviewers_map = dict()
    for review in reviews:
        for reviewer in review["reviewers"]:
            reviewers_map[reviewer["id"]] = reviewer["name"]
    
    L = list(reviewers_map.keys()) #, reviewers_map
    reviewer_index_map = dict()
    for i, r in enumerate(L):
        reviewer_index_map[r] = i
    return L, reviewer_index_map


def get_all_words(reviews):
    s = set()
    for review in reviews:
        L = re.split(r"[\s\n\t]+", review["textual-content"])
        for w in L:
            s.add(w)
    l = list(s)
    m = dict()
    for i, w in enumerate(l):
        m[w] = i
    return l, m

def remove_stop_words(word_list, word_index_map):
    pass
    # to-do

if __name__ == "__main__":

    json_file = open('Android.json', 'r')
    reviews = json.loads(json_file.read())
    json_file.close()

    reviewers, reviewer_map = get_all_reviewers(reviews)
    word_list, word_map = get_all_words(reviews)
    remove_stop_words(word_list, word_map)
    models = [dict() for _ in range(len(reviewers))]
    current_review_count = 0
    review_count_map = dict()

    def transform_review_format(rev):
        rev["textual-content"] = list(map(lambda x: word_map[x], re.split(r"[\s\n\t]+", rev["textual-content"])))
        reviewer_indices = []
        for r in rev["reviewers"]:
            reviewer_indices.append(reviewer_map[r["id"]])
        rev["reviewers"] = reviewer_indices

    def update_model(new_rev):
        word_indices = new_rev["textual-content"]
        for reviewer_index in new_rev["reviewers"]:
            review_count_map[reviewer_index] = review_count_map.get(reviewer_index, 0) + 1
            for word_index in word_indices:
                models[reviewer_index][word_index] = models[reviewer_index].get(word_index, 0) + 1
        global current_review_count
        current_review_count += 1
        
    
    def get_conf_path(rev, history_revs, reviewer_index):
        s = 0
        for old_rev in history_revs:
            c = calc_simularity(old_rev, rev)
            for index in old_rev["reviewers"]:
                if index == reviewer_index:
                    s += c
                    break
        return s

    def get_conf_text(rev, reviewer_index):
        product = 1
        for word_index in rev["textual-content"]:
            s = 0
            for k, v in models[reviewer_index].items():
                s += v
            p = models[reviewer_index].get(word_index, 0) / (s + 1)
            product *= p
        return review_count_map.get(reviewer_index, 0) / current_review_count * product
    
    for i in range(len(reviews)):
        transform_review_format(reviews[i])

    for i in range(100):
        update_model(reviews[i])
    
    for i in range(100, len(reviews)):
        L = []
        for j in range(len(reviewers)):
            c = 0.7 * get_conf_path(reviews[i], reviews[i - 100: i], reviewers[j]) + 0.3 * get_conf_text(reviews[i], j)
            L.append((j, c))
        L.sort(key=lambda x: x[1], reverse=True)
        print(L[:5], reviews[i]["reviewers"])
        update_model(reviews[i])

        
