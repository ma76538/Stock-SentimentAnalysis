#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
import os, sys
import datetime as dt
from math import sqrt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

import iohelper,sentiment
import stocktime as st

reload(sys)
sys.setdefaultencoding('utf-8')

__version__ = '0.0.1'
__license__ = 'MIT'
__author__ = 'Joshua Guo (1992gq@gmail.com)'

'''
Python Investor Sentiment Index and Shanghai Composite Index Correlation Analysis.
'''

subdir = 'Lexicons'

def main():
    global subdir
    subdir = sentiment.g_classifier_name
    if subdir.endswith('LR'):
        subdir = 'LR'
    elif subdir.endswith('NB'):
        subdir = 'NB'
    elif subdir.endswith('SVC'):
        subdir = 'SVM'
    else:
        subdir = 'Lexicons'
    print('------------------%s-------------------' % (subdir))
    review_list_day = []
    # june = 10 (after set the classifier, use its result to make correlation analysis)
    date_of_june = ['20160601', '20160602', '20160606', '20160613',
    '20160614', '20160615', '20160620', '20160622', '20160624', '20160628']
    review_list_day.extend(date_of_june)
    # review_list_day = ['20160628']  # just for test : to be removed

    up_down_cnt = 0
    cov_cnt = 0
    length = 0
    coef_max = -100
    for date in review_list_day:
        print('>>>correlation date : %s' % date)
        num, coef, length = correlation_analysis(date)
        up_down_cnt += num
        cov_cnt += abs(coef)
        if coef > coef_max:
            coef_max = abs(coef)
    up_down_cnt /= len(review_list_day)
    cov_cnt /= len(review_list_day)
    print('AVG_UP_DOWN_NUM:%s\tCOEF_AVG:%.2f\tCOEF_MAX:%.2f' % (format(up_down_cnt / length, '.2%'), cov_cnt, coef_max))

# -----------------------------------------------------------------------------
def correlation_analysis(date):
    '''
    correlating shindex_seq with saindex_seq
    return:multi-value(num, coef)
    '''

    # Analysis 1 : up down statistics
    num = up_down_num_statistics(date)

    # Analysis 2 : seq_process - index sum sequence
    shindex_seq = iohelper.read_pickle2objects(date, 'shindex_seq')  # shanghai composite index sequence
    if len(shindex_seq) == 50:
        shindex_seq.pop(25)
        shindex_seq.pop(0)
    shindex_seq = [float(index) for index in shindex_seq]
    saindex_seq = []    # sentiment index sequence
    tmp = iohelper.read_pickle2objects(date, 'saindex_seq')
    if len(tmp) == 50:
        tmp.pop(25)
        tmp.pop(0)
    tmp = [float(index) for index in tmp]
    for i in xrange(len(tmp)):
        saindex_seq.append(sum(tmp[0:i]))

    # time series day
    tick_seq = get_tick_time_series()
    if (len(tick_seq) == 50):
        tick_seq.pop(25)
        tick_seq.pop(0)

    # data normalization_min_max
    # shindex_seq = normalization_min_max(shindex_seq)
    # saindex_seq = normalization_min_max(saindex_seq)
    # data normalization_z-score
    shindex_seq = normalization_zero_mean(shindex_seq)
    saindex_seq = normalization_zero_mean(saindex_seq)

    # tick_seq = tick_seq[1:47]        # two 5-min forward
    # shindex_seq = shindex_seq[1:47]  # two 5-min forward
    # saindex_seq = saindex_seq[0:46]  # two 5-min forward to show the sentiment

    # tick_seq = tick_seq[2:47]        # three 5-min forward
    # shindex_seq = shindex_seq[2:47]  # three 5-min forward
    # saindex_seq = saindex_seq[0:45]  # three 5-min forward to show the sentiment

    print('sh day index : %s %d' % (shindex_seq, len(shindex_seq)))
    print('sa day index : %s %d' % (saindex_seq, len(saindex_seq)))
    print('ti day index : %s %d' % (tick_seq, len(tick_seq)))

    coef = pearson_corr(shindex_seq, saindex_seq)
    print(coef)
    plot_index_and_sentiment(tick_seq, shindex_seq, saindex_seq, date)
    return num, coef, len(tick_seq)

def up_down_num_statistics(date):
    shindex_seq = []
    tmp = iohelper.read_pickle2objects(date, 'shindex_seq')
    if len(tmp) == 50:
        tmp.pop(25)
        tmp.pop(0)
    tmp = [float(index) for index in tmp]
    for i in range(len(tmp)):
        if i == 0:
            shindex_seq.append(tmp[i] - 2979.4343)   # 17 : 2870.43; 18 : 2904.8319; 23 : 2999.3628  28 ： 2979.4343
        else:
            shindex_seq.append(tmp[i] - tmp[i - 1])

    saindex_seq = iohelper.read_pickle2objects(date, 'saindex_seq')
    if len(saindex_seq) == 50:
        saindex_seq.pop(25)
        saindex_seq.pop(0)
    saindex_seq = [float(index) for index in saindex_seq]

    count = 0
    for i in range(len(shindex_seq)):
        if (shindex_seq[i] > 0 and saindex_seq[i] > 0) or (shindex_seq[i] < 0 and saindex_seq[i] < 0) or (shindex_seq[i] == 0 and saindex_seq[i] == 0):
            count += 1
    print('up down common numbers : %d' % count)
    return count

def normalization_min_max(datalist):
    '''
    normalization : min_max
    '''
    dmax = max(datalist)
    dmin = min(datalist)
    list_tmp = [(x - dmin) / (dmax - dmin) for x in datalist]
    return list_tmp

def normalization_zero_mean(datalist):
    '''
    normalization : zero_mean
    '''
    D = pd.Series(datalist)
    mean = D.mean()
    std = D.std()
    print("before convert : mean and std " , mean, std)
    list_tmp = [(x - mean) / std for x in datalist]
    return list_tmp

def pearson_corr(shindex_seq, saindex_seq):
    S1 = pd.Series(shindex_seq)
    S2 = pd.Series(saindex_seq)
    corr = S1.corr(S2, method = 'pearson')
    return corr

def get_tick_time_series():
    tick_seq = []
    opentime1 = st.opentime1
    midclose = st.midclose
    opentime2 = st.opentime2
    closetime = st.closetime

    tick_delta = dt.timedelta(minutes=5)
    tick_now = opentime1

    while True:
        if (tick_now >= opentime1 and tick_now <= midclose) or (tick_now >= opentime2 and tick_now <= closetime):
            hour = tick_now.hour
            minute = tick_now.minute
            tick = hour * 100 + minute
            tick_seq.append(tick)
            tick_now += tick_delta
        elif tick_now > midclose and tick_now < opentime2:
            tick_now = opentime2
        elif tick_now > closetime:
            break
    return tick_seq

def plot_index_and_sentiment(tick_seq, shindex_seq, sentiment_seq, date):
    if len(tick_seq) != len(shindex_seq) or len(tick_seq) != len(sentiment_seq):
        print('error(plot) : three sequence length is not same')
        return

    x = range(len(shindex_seq))
    labels = tick_seq
    y1 = shindex_seq
    y2 = sentiment_seq

    def format_fn(tick_val, tick_pos):
        if int(tick_val) in x:
            return labels[int(tick_val)]
        else:
            return ''

    fig = plt.figure(figsize=(12,8))
    p1 = fig.add_subplot(111)
    p1.xaxis.set_major_formatter(FuncFormatter(format_fn))
    p1.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=12))
    delta = shindex_seq[len(shindex_seq) - 1] - shindex_seq[0]
    if delta > 0:
        p1.plot(x, y1, label="$SCI$", color="red", linewidth=1)
    else:
        p1.plot(x, y1, label="$SCI$", color="green", linewidth=1)
    p1.plot(x, y2, 'b--', label="$ISI$", color="blue", linewidth=1)

    plt.title("Shanghai Composite Index(SCI) & Investor Sentiment Index(ISI)")
    plt.xlabel("Time(5min)")
    plt.ylabel("Index Value")
    plt.legend()
    # plt.show()
    global subdir
    filepath = './Pic/' + subdir + '/' + date + '.png'
    plt.savefig(filepath)

if __name__ == '__main__':
    main()
