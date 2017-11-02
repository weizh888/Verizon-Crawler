#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
import csv
import json

import requests
from pprint import pprint
import pandas as pd
from dateutil import parser
import numpy as np


# from pyspark import SparkContext
# from pyspark.streaming import StreamingContext
# from pyspark.sql import HiveContext
# from apscheduler.schedulers.blocking import BlockingScheduler
# import socket

def crawl_reviews():

    # Check total reviews number

    review_offset = 0
    page_review_limit = 30
    callback = 'test'

    # Check total number of reviews so far (sort by review time)

    url = \
        'https://api.bazaarvoice.com/data/batch.json?passkey=e8bg3vobqj42squnih3a60fui&apiversion=5.5&displaycode=6543-en_us&resource.q0=reviews&filter.q0=isratingsonly%3Aeq%3Afalse&filter.q0=productid%3Aeq%3Adev5800066&filter.q0=contentlocale%3Aeq%3Aen_US&sort.q0=submissiontime%3Adesc&stats.q0=reviews&filteredstats.q0=reviews&include.q0=authors%2Cproducts%2Ccomments&filter_reviews.q0=contentlocale%3Aeq%3Aen_US&filter_reviewcomments.q0=contentlocale%3Aeq%3Aen_US&filter_comments.q0=contentlocale%3Aeq%3Aen_US&limit.q0={}&offset.q0={}&limit_comments.q0=3&callback={}'.format(page_review_limit,
            review_offset, callback)

    response = requests.get(url)
    json_string = response.content[len(callback) + 1:-1]
    json_data = json.loads(json_string)

    # Get the number of total reviews so far for this product

    numReviews = json_data['BatchedResults']['q0']['TotalResults']
    print 'Found {} reviews in total.'.format(numReviews)

    # Useful keys: ProductId, Title, ReviewText, SubmissionTime, UserNickname, Rating

    review_fields = [
        'Device',
        'Title',
        'ReviewText',
        'SubmissionTime',
        'UserNickname',
        'Rating',
        ]

    # Create a device dictionary - 'ProductId': 'Device'

    device_dict = {'dev5800066': 'Samsung Galaxy s7'}
    (device, title, review) = ([], [], [])
    (publishtime, author, rating) = ([], [], [])

    print 'Start to crawl reviews.'
    start_time = time.time()
    while True:

        # sort by review time

        url = \
            'https://api.bazaarvoice.com/data/batch.json?passkey=e8bg3vobqj42squnih3a60fui&apiversion=5.5&displaycode=6543-en_us&resource.q0=reviews&filter.q0=isratingsonly%3Aeq%3Afalse&filter.q0=productid%3Aeq%3Adev5800066&filter.q0=contentlocale%3Aeq%3Aen_US&sort.q0=submissiontime%3Adesc&stats.q0=reviews&filteredstats.q0=reviews&include.q0=authors%2Cproducts%2Ccomments&filter_reviews.q0=contentlocale%3Aeq%3Aen_US&filter_reviewcomments.q0=contentlocale%3Aeq%3Aen_US&filter_comments.q0=contentlocale%3Aeq%3Aen_US&limit.q0={}&offset.q0={}&limit_comments.q0=3&callback={}'.format(page_review_limit,
                review_offset, callback)

        response = requests.get(url)
        json_string = response.content[len(callback) + 1:-1]
        json_data = json.loads(json_string)

        crawl_count = 0
        for elem in json_data['BatchedResults']['q0']['Results']:
            device.append(device_dict[elem['ProductId']])
            title.append(elem['Title'].strip())
            review.append(' '.join(elem['ReviewText'].strip().split()))  # remove spaces, lines in the review text
            publishtime.append(parser.parse(elem['SubmissionTime'
                               ]).date())
            author.append(elem['UserNickname'])
            rating.append(int(elem['Rating']))
            crawl_count += 1
        print 'Crawled {} reviews ({} in total) at {}.'.format(crawl_count,
                len(review), datetime.now().time())

        if len(device) >= numReviews:
            end_time = time.time()
            print 'Spent {} seconds to crawl all the reviews using API.'.format(end_time
                    - start_time)
            break
        else:
            review_offset += page_review_limit

    all_reviews = pd.DataFrame({
        'Device': device,
        'Title': title,
        'ReviewText': review,
        'SubmissionTime': publishtime,
        'UserNickname': author,
        'Rating': rating,
        }, columns=review_fields)

    all_reviews.to_csv(r"results/quiz2_1_api.csv", index=False,
                       encoding='utf-8')


    # pprint(all_reviews)

if __name__ == '__main__':

    crawl_reviews()
