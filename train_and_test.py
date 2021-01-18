
import re
import json
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import stopwords
import logging
import argparse

from model import TIEModel
if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews_file", required=True, help="the input JSON file containing the reviews")
    parser.add_argument("--output_file", required=True, help="the file to output the results")
    parser.add_argument("--model_file", required=True, help="the file to store the model")
    args = parser.parse_args()

    json_file = open(args.reviews_file, 'r')
    reviews = json.loads(json_file.read())
    json_file.close()

    stemmer = LancasterStemmer()

    def get_all_reviewers(reviews):
        reviewer_set = set()
        for review in reviews:
            for reviewer in review["reviewers"]:
                reviewer_set.add(reviewer["id"])
        return list(reviewer_set)

    def is_word_useful(word):
        for c in word:
            if c.isdigit():
                return False
        if "http://" in word or "https://" in word:
            return False
        return True

    def word_stem(word):
        if word.endswith('.') or word.endswith(',') or word.endswith(':') or word.endswith('\'') or word.endswith('\"'):
            word = word[:-1]
        if word.startswith(',') or word.startswith('.') or word.startswith(':') or word.startswith('\'') or word.startswith('\"'):
            word = word[1:]
        return stemmer.stem(word)

    def split_text(txt):
        splitted_words = list(
            map(lambda x: word_stem(x),
                filter(lambda x: is_word_useful(x), re.split(r"[\s\n\t]+", txt))
            )
        )
        return splitted_words

    def get_all_words(reviews):
        s = set()
        for review in reviews:
            for w in split_text(review["textual-content"]):
                s.add(w)
        l = list(s)
        return l

    model = TIEModel(word_list=get_all_words(reviews), reviewer_list=get_all_reviewers(reviews), alpha=0.7, M=50, recommended_count=1000, text_splitter=split_text)

    mrr_accumulation = 0
    is_recomm_accumulation_top_10 = 0
    is_recomm_accumulation_top_5 = 0
    is_recomm_accumulation_top_3 = 0
    is_recomm_accumulation_top_1 = 0
    current_predicted = 0

    i = 0
    while i < len(reviews):
        if i + 1 == len(reviews):
            break
        model.update(reviews[i])
        recommended_reviewers = model.recommend(reviews[i + 1])
        actual_reviewers = list(map(lambda x: x["id"], reviews[i + 1]["reviewers"]))
        
        logging.info("Progress: {}/{} reviews".format(i + 1, len(reviews)))
        logging.info("ID: {}".format(reviews[i + 1]["id"]))
        logging.info("Recommended: {}".format(recommended_reviewers[:10]))
        logging.info("Actual: {}".format(actual_reviewers))
        current_predicted += 1

        is_recomm_top_10 = 0
        is_recomm_top_5 = 0
        is_recomm_top_3 = 0
        is_recomm_top_1 = 0
        for r in actual_reviewers:
            if r in recommended_reviewers[:10]:
                is_recomm_top_10 = 1
            if r in recommended_reviewers[:5]:
                is_recomm_top_5 = 1
            if r in recommended_reviewers[:3]:
                is_recomm_top_3 = 1
            if r == recommended_reviewers[0]:
                is_recomm_top_1 = 1
        is_recomm_accumulation_top_10 += is_recomm_top_10
        is_recomm_accumulation_top_5 += is_recomm_top_5
        is_recomm_accumulation_top_3 += is_recomm_top_3
        is_recomm_accumulation_top_1 += is_recomm_top_1

        top10acc = is_recomm_accumulation_top_10 / current_predicted
        top5acc = is_recomm_accumulation_top_5 / current_predicted
        top3acc = is_recomm_accumulation_top_3 / current_predicted
        top1acc = is_recomm_accumulation_top_1 / current_predicted

        logging.info('Top-10 Predict Accuracy: %.2f', top10acc)
        logging.info('Top-5 Predict Accuracy: %.2f', top5acc)
        logging.info('Top-3 Predict Accuracy: %.2f', top3acc)
        logging.info('Top-1 Predict Accuracy: %.2f', top1acc)
        model.update(reviews[i + 1])
        i += 2
    model.save(args.model_file)