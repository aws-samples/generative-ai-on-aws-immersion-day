# '''SEC 14 PoC library'''
#
# import os
# import re
# import json
# import glob, shutil
# from itertools import chain
# from typing import List
# from operator import itemgetter
#
#
# class bcolors:
#     RED = '\x1b[31m'
#     GREEN = '\x1B[32m'
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKCYAN = '\033[96m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'
#
# def highlight(text,words,color):
#     '''Highlight specific words in the given text'''
#     for w in words:
#         w = w.strip()
#         if w:
#             # Might be gaps between words. Capture entire
#             # span between tokens: A...B....C
#             pattern = re.escape(w).replace('\\ ','.*?')
#             # print(pattern)
#             # replace ignore case
#             text = re.sub(r'(?i)({})'.format(pattern), color + '\\1' + bcolors.ENDC, text)
#     return text
#
# # ----------------------------------------
#
# def preprocess_context(s):
#     s = re.sub(r'\n',' ',s) # newline
#     s = re.sub(r'^\s+','',s) # leading spaces
#     s = re.sub(r'\s+$','',s) # ending spaces
#     s = re.sub(r'\s+',' ',s) # multiple space
#     s = s + '.' if s[-1] != '.' else s
#     return s
#
#
# def iterate_corpus(directory, datapoint):
#     '''Iterate corpus and yield (context,question,answer) tuples'''
#
#     for filename in sorted(os.listdir(directory)):
#         if filename.endswith(".txt"):
#             context = read_text(directory+filename)
#             context = preprocess_context(context)
#
#             filemeta = filename.replace('.txt','.json')
#             metadata = read_json(directory+filemeta)
#
#             filelabel = filename.replace('.txt','.label.json')
#             labels = read_jsonl(directory+filelabel)
#             label = labels[0]
#
#             question = '<MAKE YOUR QUESTION>'
#             answer = label[datapoint]
#
#             yield \
#                 filename,\
#                 metadata,\
#                 context,\
#                 question,\
#                 answer
#
# def append_metadata(results: List[dict], metadata: dict):
#     for j in results:
#         j.update(
#             dict((k,v)
#                  for k,v in metadata.items()
#                  if k in ['DOCID','SEC_ACCESS_NUM','SEQ','MEMBER_NAME','FORMAT','FNAME']))
#
#
# def similar_or_contains(a,b,threshold=80):
#     '''Fuzzy comparison by fuzzywuzzy or containing'''
#
#     from fuzzywuzzy import fuzz
#
#     a = a.lower()
#     b = b.lower()
#
#     score = fuzz.ratio(a,b)
#
#     if score >= threshold:
#         return score
#     elif b in a or a in b:
#         return 99
#     else:
#         # Sort by tokens
#         a = ' '.join(sorted(a.split()))
#         b = ' '.join(sorted(b.split()))
#         score = max(score,fuzz.ratio(a,b))
#         return score
#
# def evaluate(df,datapoint,msg='',pad=0,verbose=True):
#     '''Taken from Broadridge codebase'''
#
#     n_san = df['SEC_ACCESS_NUM'].nunique()
#     n_rec = df.shape[0]
#
#     assert df[datapoint+'_ERROR'].notna().all()
#
#     tp = (df[datapoint+'_ERROR'] == 'TP').sum()
#     fp = (df[datapoint+'_ERROR'] == 'FP').sum()
#     fn = (df[datapoint+'_ERROR'] == 'FN').sum()
#     tn = (df[datapoint+'_ERROR'] == 'TN').sum()
#
#     assert n_rec == tp + fp + fn + tn
#
#
#     precision = (tp / (tp + fp)) if (tp + fp) else 0.0
#     recall = (tp / (tp + fn)) if (tp + fn) else 0.0
#     acc = ((tp + tn) / n_rec) if n_rec else 0
#
#     if verbose:
#         print('{}{}: '
#         'pr={:5.1%} recall={:5.1%} acc={:5.1%} |'
#         'docs={} |'
#         'tp={} fp(extra)={} fn(miss)={} tn={} |'
#         'err={}'.format(
#             datapoint[:pad].ljust(pad) if pad else datapoint,
#             msg,
#             precision,recall,acc,
#             # n_san,n_rec,
#             n_rec,
#             tp,fp,fn,tn,fp+fn))
#
# def to_entities(s,delimeter,split=True,IDK=None):
#     return tokenize(s,delimeter,split,IDK)
#
# def tokenize(s,delimeter,split=True,IDK=None):
#     '''Convert textual response into a list of spans'''
#
#     def dedup(xs):
#         '''Dedup and keep order'''
#         seen = set()
#         seen_add = seen.add
#         return [x for x in xs if not (x in seen or seen_add(x))]
#
#     def clean(s):
#         s = re.sub(r'[\.\,\;]',' ',s) # dot
#         s = re.sub(r'^\s+','',s) # leading spaces
#         s = re.sub(r'\s+$','',s) # ending spaces
#         s = re.sub(r'\s+',' ',s) # multiple space
#         return s
#
#     def stop_words_pattern():
#         stop_words = ["\'s",'and','of','the','inc','ltd','plc','llp','company']
#
#         p = r'{}'.format('|'.join(
#             chain.from_iterable(
#                 [r'\b'+ w + r'$',
#                  r'\b'+ w + r'\b',
#                 ]
#                 for w in stop_words
#             )))
#
#         return re.compile(p,flags=re.I)
#
#
#     s = s.lower()
#
#     if IDK:
#         s = s.replace(IDK.lower(),'')
#         s = s.replace(IDK.lower().replace('.',''),'')
#
#     s = s.replace(' and ', delimeter) # extra delimeter
#     s = re.sub(r'\(.*.\)','',s) # erase inside parenthesis
#     s = re.sub(stop_words_pattern(), '', s)
#     xs = [clean(x) for x in s.split(delimeter)]
#     xs = [x for x in xs if x]
#     xs = dedup(xs)
#
#     if not split:
#         xs = [' '.join(xs)]
#
#     return xs
#
# def compute_matches(y_true: List[str], y_pred: List[str], datapoint, verbose=False):
#     '''Match set-to-set of spans'''
#
#     matches = [] # (gt,ai)
#
#
#     tp_a_b,tp_b_a = 0,0
#     tp,tn,fn,fp = 0,0,0,0
#
#
#     y_true = [x for x in y_true if x]
#     y_pred = [x for x in y_pred if x]
#
#     # Both are empty/unknown
#     if not y_true and not y_pred:
#         tp_a_b += 1
#         tp_b_a += 1
#         matches += {datapoint+'_GT':'empty',
#                     datapoint+'_AI':'empty',
#                     datapoint+'_ERROR':'TP',
#                     datapoint+'_SCORE':100},
#
#
#     else:
#
#
#         # Match each y_true[i] to y_pred
#         for y_true_i in y_true:
#             assert y_true_i, 'Cannot be empty'
#
#             if not y_pred:
#                 fn += 1
#                 matches += {datapoint+'_GT':y_true_i,
#                             datapoint+'_AI':"",
#                             datapoint+'_ERROR':'FN',
#                             datapoint+'_SCORE':0},
#             else:
#                 # Best match
#                 y_true_i,y_pred_i,score = max((
#                             (y_true_i,y_pred_i,similar_or_contains(y_true_i,y_pred_i))
#                             for y_pred_i in y_pred),
#                     key=itemgetter(2))
#
#
#                 if score >= 80:
#                     tp_a_b += 1
#                     matches += {datapoint+'_GT':y_true_i,
#                             datapoint+'_AI':y_pred_i,
#                             datapoint+'_ERROR':'TP',
#                             datapoint+'_SCORE':score},
#
#                 else:
#                     fn += 1
#                     matches += {datapoint+'_GT':y_true_i,
#                             datapoint+'_AI':"",
#                             datapoint+'_ERROR':'FN',
#                             datapoint+'_SCORE':score},
#
#
#                     if verbose:
#                         print('FN','best match GT->AI is',score)
#                         print(' AI:',y_pred_i)
#                         print(' GT:',y_true_i)
#                         print()
#
#
#
#         # Match each y_pred[i] to y_true
#         for y_pred_i in y_pred:
#             assert y_pred_i, 'Cannot be empty'
#
#             if not y_true:
#                 fp += 1
#                 matches += {datapoint+'_GT':"",
#                             datapoint+'_AI':y_pred_i,
#                             datapoint+'_ERROR':'FP',
#                             datapoint+'_SCORE':0},
#             else:
#                 # Best match
#                 y_true_i,y_pred_i,score = max((
#                             (y_true_i,y_pred_i,similar_or_contains(y_true_i,y_pred_i))
#                             for y_true_i in y_true),
#                         key=itemgetter(2))
#
#
#                 if score >= 80:
#                     tp_b_a += 1
#                     matches += {datapoint+'_GT':y_true_i,
#                             datapoint+'_AI':y_pred_i,
#                             datapoint+'_ERROR':'TP',
#                             datapoint+'_SCORE':score},
#                 else:
#                     fp += 1
#                     matches += {datapoint+'_GT':"",
#                             datapoint+'_AI':y_pred_i,
#                             datapoint+'_ERROR':'FP',
#                             datapoint+'_SCORE':score},
#
#                     if verbose:
#                         print('FP','best match AI->GT is',score)
#                         print(' AI:',y_pred_i)
#                         print(' GT:',y_true_i)
#                         print()
#
#
#
#     tp = min(tp_a_b,tp_b_a)
#
#     if verbose:
#         print('tp={}, min({},{})'.format(tp,tp_a_b,tp_b_a))
#         print(f'fp={fp}')
#         print(f'fn={fn}')
#
#     return tp,fp,fn,matches
#
#
#
# if __name__ == "__main__":
#     main()
#
