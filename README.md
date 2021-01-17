Implementation of a paper in ICSME 2015
==============
This project implements the model ***TIE*** described in paper [Who Should Review This Change?](http://www.mysmu.edu/faculty/davidlo/papers/icsme15-review.pdf).

How to use
==============
Run `retrieve_reviews.py` to retrieve historical reviews from Gerrit systems. You can modify the variable `projects` in this file.

Here I provide 4 JSON files that contains reviews from 4 big projects. You can use these files directly.

Run `recommend_reviewers.py` to train a recommendation model and test the model at the same time. The method is described in the paper:

> The process proceeds as follows: first, we train a TIE model by using the first review, and test the trained model by using the second review, then we update the TIE model by using the second review (with its ground truth reviewers). Next, we test using the third review, and update the TIE model by using the third review, and so on.


You must run the script with these parameters shown below:

| Parameter | Description |
| --- | --- |
| *reviews_file* | the input JSON file containing the reviews |
| *output_file* | the file to output the results |

Example command:

```bash
python recommend_reviewers.py --reviews_file=Android.json --output_file=output/Android_output.json
```

Input Format
==============
Input JSON is an array that contains many review objects. Each review object contains fields `id`, `uploaded-time`, `reviewers`, `textual-content` and `changed-files`:
- Field `id` is the unique identifier of the review.
- Field `uploaded-time` is the time when the review was committed to Gerrit system.
- Field `reviewer` is an array of several reviewer object. Each reviewer object must at least contain field `id`(usually a 32-bit integer).
- Field `textual-content` is text content of the review.
- Field `changed-files` is an array of changed files.

An example is shown below:

```json
[
    {
        "id": "qt%2Fqtsensors~master~I1c0dd3dea4a0b296388f66fc44fed560da85e028",
        "uploaded-time": "2012-05-29 23:23:35.000000000",
        "reviewers": [
            {
                "id": 1000049,
                "name": "Qt Sanity Bot"
            },
            {
                "id": 1000097,
                "name": "Lincoln Ramsay"
            },
            {
                "id": 1000136,
                "name": "Lorn Potter"
            }
        ],
        "textual-content": "there is no main.qml file here. Now it shows up in creator.\n\nChange-Id: I1c0dd3dea4a0b296388f66fc44fed560da85e028\n",
        "changed-files": [
            "examples/QtSensors/QtSensors_accelbubble/QtSensors_accelbubble.pro"
        ]
    }
]
```

Output Format
==============
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
        {
            "review-id": "qt%2Fqtsensors~master~I1c0dd3dea4a0b296388e66fc44fed360da85e028",
            "result": [100003, 10013, 100014, 100055, 100023, 100011, 100033, 100004, 100008, 100009]
        },
        {
            "review-id": "qt-creator%2Fqt-creator~master~I5774d04a45f28a4e276a0ef283ce0aa5a2f2e553",
            "result": [100002, 10013, 100015, 100011, 100023, 100044, 100023, 100007, 100001, 100031]
        }
    ]
}
```

Results on 4 projects
==============

1. Statistics of collected data

| Project | Time Period | Revi. | Re. | Avg. Re. |
| --- | --- | --- | --- | --- |
| Android | 2008/10 - 2012/01 | 8958 | 802 | 2.58 |
| LibreOffice | 2012/03 - 2014/06 | 8585 | 224 | 1.54 |
| OpenStack | 2011/07 - 2012/05 | 7064 | 367 | 3.97 |
| QT | 2011/05 - 2012/05 | 24734 | 530 | 3.31 |

Here `Revi.` refers to the number of collected reviews, `Re.` refers to the number of the unique reviewers extracted from collected reviews, and `Avg.Re` refers to the average number of code reviewers per review.

2. Results

| Project | Top-10 P.A. | Top-5 P.A. | Top-3 P.A. | Top-1 P.A. | MRR |
| --- | --- | --- | --- | --- | --- |
| Android | 0.86 | 0.80 | 0.74 | 0.56 | 0.67 |
| LibreOffice | 0.89 | 0.80 | 0.74 | 0.53 | 0.66 |
| OpenStack | 0.73 | 0.41 | 0.25 | 0.06 | 0.24 |
| QT | 0.93 | 0.89 | 0.85 | 0.65 | 0.76 |

Here `P.A.` means *Prediction Accuracy*.