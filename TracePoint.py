# -*- coding: utf-8 -*-

import Alignment

import re
import math
import sys

class TracePointAlignment(object):

  def __init__(self, seq1, seq2, delta, start_seq1, start_seq2):
    self.seq1 = seq1
    self.seq2 = seq2
    self.delta = delta
    self.start_seq1 = start_seq1
    self.start_seq2 = start_seq2
    # is set by encode function
    self.tp = None

  # extract TracePoints from CIGAR-String
  def encode_cigar(self, cigar):

    count = count1 = count2 = cig_count = interval_count = 0

    end_seq1 = self.start_seq1 + len(self.seq1) - 1
    end_seq2 = self.start_seq2 + len(self.seq2) - 1

    # dynamic calculation of interval size
    dynamic = max(1,int(math.ceil(self.start_seq1/self.delta)))

    # adjustment of interval length
    interval_count = min(int(math.ceil(float(len(self.seq1)) / self.delta)), int(math.ceil(float(len(self.seq2)) / self.delta)))

    # intervals
    # initialized with 0s
    intervals = [0] * interval_count

    for i in range(0, interval_count):
      # first interval
      if i == 0:
        intervals[i] = self.start_seq1, dynamic * self.delta - 1
      # last interval
      elif i == interval_count - 1:
        intervals[i] = (dynamic + interval_count - 2) * self.delta, end_seq1
      # other intervals
      else:
        intervals[i] = (dynamic + i - 1) * self.delta, (dynamic + i) * self.delta - 1

    # create pattern for CIGAR-String
    cigar_pattern = re.compile(r"\d+[MIDNSHP=j]{1}")

    # search cigar for pattern
    tp = []
    for j in cigar_pattern.findall(cigar):
      cig_count = int(j[:-1])
      cig_symbol = j[-1]

      for i in range(0,cig_count):
        if cig_symbol == 'I':
          count1 += 1
        elif cig_symbol == 'D':
          count2 += 1
        else:
          count1 += 1
          count2 += 1

        # count until the end but ignore end of last interval as TracePoint
        if count1 == intervals[count][1] + 1 and count1 != len(self.seq1):
          tp.append(count2 - 1 + self.start_seq2)
          count += 1

    self.tp = tp

  #number of chars and '-'s in sequence  
  def count_indels_letters(self, seq):

    letter_count = 0
    indel_count = 0

    for i in range(0,len(seq)):
      if seq[i].isalpha():
        letter_count += 1
      elif seq[i] == '-':
        indel_count += 1

    return [letter_count, indel_count]

  # extract TracePoints from alignment
  def encode(self):
  
    indels_in_seq2 = all_chars_in_seq1 = interval_count = 0

    # number of chars in sequences
    letters_in_seq1 = self.count_indels_letters(self.seq1)[0]
    letters_in_seq2 = self.count_indels_letters(self.seq2)[0]

    # Trace Point Array
    tp = []

    end_seq1 = letters_in_seq1 - 1
    end_seq2 = letters_in_seq2 - 1

    # dynamic calculation of interval size
    dynamic = max(1,int(math.ceil(self.start_seq1/self.delta)))

    # adjustment of interval length
    interval_count = min(int(math.ceil(float(len(self.seq1)) / self.delta)), int(math.ceil(float(len(self.seq2)) / self.delta)))

    # intervals
    intervals = [0] * interval_count

    for i in range(0, interval_count):
      # first interval
      if i == 0:
        intervals[i] = self.start_seq1, dynamic * self.delta - 1
      # last interval
      elif i == interval_count - 1:
        intervals[i] = (dynamic + interval_count - 2) * self.delta, end_seq1
      # other intervals
      else:
        intervals[i] = (dynamic + i - 1) * self.delta, (dynamic + i) * self.delta - 1

    start  = tmp = 0

    for i in range(0,len(intervals)):
    
      # ignore last interval
      if i == len(intervals) - 2:
        break
      else:

        # Anzahl der Buchstaben an den Enden der Sequenzen
        rest1 = self.count_indels_letters(self.seq1[all_chars_in_seq1:end_seq1])[0]
        rest2 = self.count_indels_letters(self.seq2[all_chars_in_seq1:end_seq2])[0]

        # break condition
        if rest1 != 0 and rest2 != 0:
          # first delta letters in alignment.seq1
          while self.count_indels_letters(self.seq1[start:all_chars_in_seq1])[0] != self.delta:
            all_chars_in_seq1 += 1

        # count gaps in seq2
        indel_count = self.count_indels_letters(self.seq2[start:all_chars_in_seq1])[1]
        indels_in_seq2 += indel_count
        tp.append(all_chars_in_seq1 - indels_in_seq2 - 1 + self.start_seq2)
        tmp = start
        start = all_chars_in_seq1
        all_chars_in_seq1 = tmp

    self.tp = tp

    self.store_tp_aln()

  # create new intervals from TracePoints and calculate new alignment
  def decode(self, seq1, seq2, delta, tp, start_seq1, start_seq2):

    new_seq1 = new_seq2 = ""
    
    aln = Alignment.Alignment(seq1, seq2, start_seq1, start_seq2)

    for i in range(0,len(tp)):
      
      if i == 0:

        new_seq1 += str(seq1[0:delta])
        new_seq2 += str(seq2[0:tp[i] + 1])
      
      elif i == len(tp) - 1:

        new_seq1 += str(seq1[i*delta:(i+1)*delta])
        new_seq2 += str(seq2[tp[i-1]+1:tp[i]+1])
 
        new_seq1 += str(seq1[(i+1)*delta:len(seq1)])
        new_seq2 += str(seq2[tp[i]+1:len(seq2)])

      else:
        
        new_seq1 += str(seq1[i*delta:(i+1)*delta])
        new_seq2 += str(seq2[tp[i-1]+1:tp[i] + 1])

  # store TracePointAlignment to file
  def store_tp_aln(self):
  
    with open('aln_file.txt', 'a') as file_:
      
      file_.write("%d;%d;%d;%s\n" % (self.delta, self.start_seq1, self.start_seq2, self.tp))
