import re
import json
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import stopwords
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
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

def is_word_useful(word):
    for c in word:
        if c.isdigit():
            return False
    if "http://" in word or "https://" in word:
        return False
    return True

    
def get_all_words(reviews):
    s = set()
    for review in reviews:
        for w in review["textual-content"]:
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

    json_file = open('OpenStack.json', 'r')
    reviews = json.loads(json_file.read())
    json_file.close()

    stemmer = LancasterStemmer()
    def word_stem(word):
        if word.endswith('.') or word.endswith(',') or word.endswith(':') or word.endswith('\'') or word.endswith('\"'):
            word = word[:-1]
        if word.startswith(',') or word.startswith('.') or word.startswith(':') or word.startswith('\'') or word.startswith('\"'):
            word = word[1:]
        return stemmer.stem(word)

    def process_textual_content(content):
        splitted_words = list(
            map(lambda x: word_stem(x),
                filter(lambda x: is_word_useful(x), re.split(r"[\s\n\t]+", content))
            )
        )
        return splitted_words

    for rev in reviews:
        rev["textual-content"] = process_textual_content(rev["textual-content"])
    logging.info("Word preprocessing completed.")

    reviewers, reviewer_map = get_all_reviewers(reviews)
    word_list, word_map = get_all_words(reviews)
    remove_stop_words(word_list, word_map)
    models = [dict() for _ in range(len(reviewers))]
    current_review_count = 0
    review_count_map = dict()

    logging.info('{} reviews, {} reviewers, {} words in total.'.format(len(reviews), len(reviewers), len(word_list)))
    simularity_cache = {}
    def calc_simularity(rev1, rev2):
        key = str(rev1["id"]) + "-" + str(rev2["id"])
        if key in simularity_cache:
            return simularity_cache[key]
        changed_files1 = rev1["changed-files"][:1000]
        changed_files2 = rev2["changed-files"][:1000]
        if len(changed_files1) == 0 or len(changed_files2) == 0:
            return 0
        sum_score = 0
        for f1 in changed_files1:
            s1 = set(f1.split('/'))
            for f2 in changed_files2:
                s2 = set(f2.split('/'))
                sum_score += (len(s1 & s2)) / max(len(s1), len(s2))
        ret = sum_score / (len(changed_files1) * len(changed_files2) + 1)
        simularity_cache[key] = ret
        return ret

    def transform_review_format(rev, rev_id):
        rev["textual-content"] = list(map(lambda x: word_map[x], rev["textual-content"]))
        reviewer_indices = []
        for r in rev["reviewers"]:
            reviewer_indices.append(reviewer_map[r["id"]])
        rev["reviewers"] = reviewer_indices
        rev["id"] = rev_id

    def update_model(new_rev):
        word_indices = new_rev["textual-content"]
        for reviewer_index in new_rev["reviewers"]:
            review_count_map[reviewer_index] = review_count_map.get(reviewer_index, 0) + 1
            for word_index in word_indices:
                models[reviewer_index][word_index] = models[reviewer_index].get(word_index, 0) + 1
        global current_review_count
        current_review_count += 1
        
    
    def get_conf_path(rev, history_rev_start, history_rev_end, reviewer_index):
        s = 0
        for i in range(history_rev_start, history_rev_end):
            old_rev = reviews[i]
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
            p = models[reviewer_index].get(word_index, 1e-9) / (s + 1)
            product *= p
        return review_count_map.get(reviewer_index, 0) / current_review_count * product
    
    for i in range(len(reviews)):
        transform_review_format(reviews[i], i)

    for i in range(100):
        update_model(reviews[i])
    
    mrr_accumulation = 0
    is_recomm_accumulation_top_10 = 0
    is_recomm_accumulation_top_5 = 0
    is_recomm_accumulation_top_3 = 0
    is_recomm_accumulation_top_1 = 0
    i = 100
    current_predicted = 0
    while i < len(reviews):
        update_model(reviews[i])
        if i + 1 == len(reviews):
            break
        L = []
        for j in range(len(reviewers)):
            c = 0.7 * get_conf_path(reviews[i + 1], i - 100 + 1, i + 1, reviewers[j]) + 0.3 * get_conf_text(reviews[i + 1], j)
            L.append((j, c))
        L.sort(key=lambda x: x[1], reverse=True)
        # logging.info(print(L[:10]))
        L = list(map(lambda x: x[0], L))

        logging.info("Review ID: {}".format(i + 1))
        logging.info("Recommended: {}".format(L[:10]))
        logging.info("Actual: {}".format(reviews[i + 1]["reviewers"]))
        current_predicted += 1
        rank = -1
        for k in range(len(L)):
            if L[k] in reviews[i + 1]["reviewers"]:
                rank = k
                break
        mrr_accumulation += 1 / (rank + 1)
        is_recomm_top_10 = 0
        is_recomm_top_5 = 0
        is_recomm_top_3 = 0
        is_recomm_top_1 = 0
        for r in reviews[i + 1]["reviewers"]:
            if r in L[:10]:
                is_recomm_top_10 = 1
            if r in L[:5]:
                is_recomm_top_5 = 1
            if r in L[:3]:
                is_recomm_top_3 = 1
            if r == L[0]:
                is_recomm_top_1 = 1
        is_recomm_accumulation_top_10 += is_recomm_top_10
        is_recomm_accumulation_top_5 += is_recomm_top_5
        is_recomm_accumulation_top_3 += is_recomm_top_3
        is_recomm_accumulation_top_1 += is_recomm_top_1
        update_model(reviews[i + 1])

        logging.info('Top-10 Predict Accuracy: %.2f', is_recomm_accumulation_top_10 / current_predicted)
        logging.info('Top-5 Predict Accuracy: %.2f', is_recomm_accumulation_top_5 / current_predicted)
        logging.info('Top-3 Predict Accuracy: %.2f', is_recomm_accumulation_top_3 / current_predicted)
        logging.info('Top-1 Predict Accuracy: %.2f', is_recomm_accumulation_top_1 / current_predicted)
        logging.info('MRR: %.2f', mrr_accumulation / current_predicted)
        i += 2
