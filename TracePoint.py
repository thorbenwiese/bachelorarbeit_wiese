import Alignment

import re
import math
import sys

class TracePointAlignment(object):

  def __init__(self, seq1, seq2, delta, cigar, start_seq1, end_seq1, start_seq2, end_seq2):
    self.seq1 = seq1
    self.seq2 = seq2
    self.delta = delta
    self.start_seq1 = start_seq1
    self.start_seq2 = start_seq2
    self.end_seq1 = end_seq1
    self.end_seq2 = end_seq2
    self.cigar = cigar
    if len(cigar) > 0:
      self.tp = self.encode()

  # extract TracePoints from CIGAR-String
  def encode(self):

    count = count1 = count2 = cig_count = interval_count = 0

    # dynamic calculation of interval size
    dynamic = max(1,int(math.ceil(self.start_seq1/self.delta)))

    # adjustment of interval length
    interval_count = min(int(math.ceil(float(len(self.seq1)) / self.delta)), 
                         int(math.ceil(float(len(self.seq2)) / self.delta)))

    # intervals
    # initialized with 0s
    intervals = [0] * interval_count

    for i in range(0, interval_count):
      # first interval
      if i == 0:
        intervals[i] = self.start_seq1, dynamic * self.delta - 1
      # last interval
      elif i == interval_count - 1:
        intervals[i] = (dynamic + interval_count - 2) * self.delta, self.end_seq1-1
      # other intervals
      else:
        intervals[i] = (dynamic + i - 1) * self.delta, (dynamic + i) * self.delta - 1

    # create pattern for CIGAR-String
    cigar_pattern = re.compile(r"\d+[MIDNSHP=j]{1}")

    # search cigar for pattern
    tp = []
    for j in cigar_pattern.findall(self.cigar):
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
          if count != len(intervals)-1:
            count += 1

    return tp

  # create new intervals from TracePoints and calculate new alignment
  def decode(self, seq1, seq2, delta, tp, start_seq1, end_seq1, start_seq2, end_seq2):

    # calculate CIGAR of intervals
    cigar = ""
    
    aln = Alignment.Alignment(seq1, seq2, start_seq1, end_seq1, start_seq2,end_seq2)

    for i in range(0,len(tp)):
      
      if i == 0:

        aln_seq1, aln_seq2 = aln.calculate(seq1[0:delta],seq2[0:tp[i]+1])
        cigar += aln.calc_cigar(aln_seq1, aln_seq2)
      
      elif i == len(tp) - 1:
 
        aln_seq1, aln_seq2 = aln.calculate(seq1[i*delta:len(seq1)],seq2[tp[i-1]+1:len(seq2)])
        cigar += aln.calc_cigar(aln_seq1, aln_seq2)

      else:
        
        aln_seq1, aln_seq2 = aln.calculate(seq1[i*delta:(i+1)*delta],seq2[tp[i-1]+1:tp[i] + 1])
        cigar += aln.calc_cigar(aln_seq1, aln_seq2)
   
    # calculate aln_seq with CIGAR

    cig_count = tmp1 = tmp2 = count = 0
    aln_seq1 = aln_seq2 = ""

    #neues Pattern fuer Cigar String im Format Zahl + 1 Buchstabe aus {M,I,D,N,S,H,P}
    cigar_pattern = re.compile(r"\d+[MIDNSHP=X]{1}")
    #in cigar nach pattern suchen
    for element in cigar_pattern.findall(cigar):
      count+=1

      tmp1 += cig_count
      tmp2 += cig_count
      cig_count = int(element[:-1])
      cig_symbol = element[-1]

      if cig_symbol == 'M':
        aln_seq1 += str(seq1[tmp1:tmp1+cig_count])
        aln_seq2 += str(seq2[tmp2:tmp2+cig_count])

      elif cig_symbol == 'I':
        aln_seq1 += str(seq1[tmp1:tmp1+cig_count])
        aln_seq2 += str("-"*cig_count)
        tmp2-=cig_count

      elif cig_symbol == 'D':
        aln_seq1 += str("-"*cig_count)
        aln_seq2 += str(seq2[tmp2:tmp2+cig_count])
        tmp1 -= cig_count

    aln.show_aln(aln_seq1, aln_seq2)

  # store TracePointAlignment to file
  def store_tp_aln(self,mode):
  
    with open('aln_file.txt', mode) as file_:
      
      file_.write("%d;%d;%d;%d;%d;%s\n" % (self.delta, self.start_seq1, 
                  self.end_seq1, self.start_seq2, self.end_seq2, self.tp))
