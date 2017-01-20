# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 23:13:00 2017

@author: Lucinda
"""

import re

hand = open('/Users/Lucinda/Desktop/regex_sum_353505.txt')
numlist = list()
sum1 =0
for line in hand:
    line = line.rstrip()
    stuff = re.findall('[0-9]+', line)
    for i in stuff:
        num = float(i)             
        sum1 += num


print(sum1)    
