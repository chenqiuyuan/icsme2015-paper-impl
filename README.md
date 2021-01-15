### Implementation of a paper in ICSME 2015

This project implements the model ***TIE*** described in paper [Who Should Review This Change?](https://).

#### How to use

Run `retrieve_reviews.py` to retrieve historical reviews from gerrit systems. You can modify the variable `projects` in this file.

Here I provide 4 JSON files that contains reviews from 4 big projects. You can use these files directly.

Run `recommend_reviewers.py` to train a recommendation model and test the model at the same time. The method is described in the paper:

> The process proceeds as follows: first, we train a TIE model by using the first review, and test the trained model by using the second review, then we update the TIE model by using the second review (with its ground truth reviewers). Next, we test using the third review, and update the TIE model by using the third review, and so on.


You must run the script with these parameters shown below:

| Parameter | Description |
| --- | --- |
| *reviews_file* | the input JSON file containing the reviews |
| *output_file* | the file to output the results |

#### Input Format

Input JSON is an array that contains many review objects. Each review object contains fields `uploaded-time`, `reviewers`, `textual-content` and `changed-files`:
- Field `uploaded-time` is the time when the review was committed to gerrit system.
- Field `reviewer` is an array of several reviewer object. Each reviewer object must at least contain field `id`(usually a 32-bit integer).
- Field `textual-content` is text content of the review.
- Field `changed-files` is an array of changed files.

An example is shown below:

```json
[
    {
        "uploaded-time": "2012-03-06 10:46:42.000000000",
        "reviewers": [
            {
                "id": 1000003,
                "name": "Norbert Thiebaud"
            }
        ],
        "textual-content": "attempt fix of hang on base close, due to solarmutex deadlock on join\n\nChange-Id: I602cfbcee74e6b156ae4809255b33a1ca94763c7\n",
        "changed-files": [
            "framework/inc/dispatch/closedispatcher.hxx",
            "framework/source/dispatch/closedispatcher.cxx"
        ]
    }
]
```

#### Output Format

The output JSON object contains top-10 recommended reviewers' IDs for all reviews, together with statistics.

An example is shown below:

```json
{
    "top1-accuracy": 0.50,
    "top3-accuracy": 0.60,
    "top5-accuracy": 0.80,
    "top10-accuracy": 0.92,
    "mrr": 0.63,
    "recommendation-results": [
        [100003, 10013, 100014, 100055, 100023, 100011, 100033, 100004, 100008, 100009],
        [100002, 10013, 100015, 100011, 100023, 100044, 100023, 100007, 100001, 100031],
    ]
}
```




