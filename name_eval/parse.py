import os
import sys
import sentencepiece as spm
import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet

import json
import copy

import re

sp = spm.SentencePieceProcessor()
sp.load('./segmentation_model/segmentation.model')
lem = WordNetLemmatizer()

def find_v(text):
    if type(text) == list:
        text = text[0]
    pattern = r'v\d'
    if bool(re.search(pattern, text)) == True:
        return True

    pattern = r'a\d'
    return bool(re.search(pattern, text))

def main():
    answername = '../inputs/' + str(sys.argv[2]) + '_' +  str(sys.argv[3]) + '_input.json'
    outputname = '../output_result/' + str(sys.argv[1]) + '_' + str(sys.argv[2]) + '_' + str(sys.argv[3]) + '.json'

    fp = open(answername, 'r')
    answer_gt = json.load(fp)

    fp = open(outputname, 'r')
    output_gt = json.load(fp)

    gt_func_cnt = 0
    gt_var_cnt = 0

    for i in answer_gt:
        if i in output_gt and len(output_gt[i]) == 0:
            continue
        answers = answer_gt[i]["answer"]
        for answer in answers:
            if "FUNC" in answer and "sub_" not in answers[answer] and len(answers[answer]) != 0:
                gt_func_cnt += 1
            if "VAR" in answer and "undefined" not in answers[answer] and "local_" not in answers[answer] and "None" not in answers[answer] and "DAT_" not in answers[answer]:
                if  find_v(answers[answer]) == False and len(answers[answer]) != 0:
                    gt_var_cnt += 1

    temp = {}
    for idx in output_gt.keys():
        answer = {}
        if len(output_gt[idx]) == 0:
            continue



        lines = output_gt[idx].split('\n')
        for line in lines:
            line = line.replace('`', '')
            line = line.replace('*', '')
            line = line.replace('-', '')
            line = line.replace(' ', '')

            if "Not specified" in line:
                continue

            if len(line.split(':')) != 2:
                continue


            target = line.split(':')[0]
            value = line.split(':')[1].split('<')[0]
            if len(value) == 0:
                continue
            if "VAR" in target or "FUNC" in target or "TYPE" in target and target not in answer:
                answer[target] = value

        temp[idx] = answer

    output_gt = copy.deepcopy(temp)

    var_total = 0
    var_cor = 0
    var_miss = 0
    func_total = 0
    func_cor = 0
    func_miss = 0
    type_total = 0
    type_miss = 0

    all_output = []
    var_output = []
    type_output = []
    func_output = []

    cnt = 0
    for idx in output_gt.keys():
        if len(output_gt[idx]) != 0:
            for answer in answer_gt[idx]["answer"]:
                if len(answer) == 0:
                    continue
                if "VAR" in answer:
                    if "undefined" in answer_gt[idx]["answer"][answer] or "local_" in answer_gt[idx]["answer"][answer] or "None" in answer_gt[idx]["answer"][answer] or "DAT_" in answer_gt[idx]["answer"][answer]:
                        continue

                        # IDA pro
                    if find_v(answer_gt[idx]["answer"][answer]) == True:
                        continue

                if "FUNC" in answer:
                    if "sub_" in answer_gt[idx]["answer"][answer]:
                        continue

                cnt += 1
                if answer in output_gt[idx]:
                    result = ""
                    result += func_name_preprocessing(output_gt[idx][answer])
                    result += ","
                    if isinstance(answer_gt[idx]["answer"][answer], list):
                        answer_gt[idx]["answer"][answer] = answer_gt[idx]["answer"][answer][0]
                    result += func_name_preprocessing(answer_gt[idx]["answer"][answer])
                    result += ",["
                    prob = [1.0000]*len(func_name_preprocessing(answer_gt[idx]["answer"][answer]).split())
                    result += " ".join(str(e) for e in prob)
                    result += "]\n"
                    all_output.append(result)

                    ## without codewordnet
                    if "FUNC" in answer:
                        if (output_gt[idx][answer] == answer_gt[idx]["answer"][answer]):
                            func_cor += 1
                    elif "VAR" in answer:
                        if (output_gt[idx][answer] == answer_gt[idx]["answer"][answer]):
                            var_cor += 1

                    if "FUNC" in answer:
                        func_total += 1
                        if answer not in output_gt[idx]:
                            func_miss += 1
                        else:
                            func_output.append(result)
                    elif "TYPE" in answer:
                        type_total += 1
                        if answer not in output_gt[idx]:
                            type_miss += 1
                        else:
                            type_output.append(result)
                    elif "VAR" in answer:
                        var_total += 1
                        if answer not in output_gt[idx]:
                            var_miss += 1
                        else:
                            var_output.append(result)

    # normal analysis
    #fp = open('evaluation_input_' + str(sys.argv[1]) + '_' +  str(sys.argv[2]) + '_' + str(sys.argv[3]) + '_func.txt', 'w')
    fp = open('evaluation_input_' + str(sys.argv[1]) + '_' +  str(sys.argv[2]) + '_func.txt', 'w')
    for line in func_output:
        fp.write(line)
    fp.close()


    # without codewordnet
    var_precision = var_cor / var_total
    var_recall = var_cor / gt_var_cnt
    var_f1 = 2 * var_precision * var_recall / (var_precision + var_recall)

    func_precision = func_cor / func_total
    func_recall = func_cor / gt_func_cnt
    func_f1 = 2 * func_precision * func_recall / (func_precision + func_recall)

    #print (f'{sys.argv[1]} {sys.argv[2]} {sys.argv[3]} {func_precision} {func_recall} {func_f1} {var_precision} {var_recall} {var_f1}')
    print (f'{sys.argv[1]} {sys.argv[2]} {sys.argv[3]} {func_f1} {var_f1}')

def func_name_segmentation(word):
    """
        Segment concatenated words into individual words
    """
    res = sp.encode_as_pieces(word)
    res[0] = res[0][1:]
    return res

def get_pos(treebank_tag):
    """
    get the pos of a treebank tag
    """
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None # for easy if-statement

def func_name_preprocessing(func_name):
    """
        Preprocess function name by:
        - tokenize whole name into words
        - remove digits
        - segment concatenated words
        - lemmatize words
    """
    #if len(func_name) <= 1 or func_name.replace('_','').replace('=','').replace('-','').replace('[','').replace(']','').isdigit() == True or len(func_name.replace('=','').replace('-','').replace('[','').replace(']','')) <= 1:
    #    return func_name
    orig_name = func_name

    # split whole name into words and remove digits
    func_name = func_name.replace('"', '')
    func_name = func_name.replace('.', '')
    func_name = func_name.replace('_', ' ')
    func_name = func_name.lower()
    tmp = ''
    for c in func_name:
        if not c.isalpha(): # filter out numbers and other special characters, e.g. '_' and digits
            tmp = tmp + ' '
        elif c.isupper():
            tmp = tmp + ' ' + c
        else:
            tmp = tmp + c
    tmp = tmp.strip()
    tmp = tmp.split(' ')

    res = []
    i = 0
    while i < len(tmp):
        cap = ''
        t = tmp[i]

        # haies of capital letters: e.g., SHA, MD
        while i < len(tmp) and len(tmp[i]) == 1:
            cap = cap + tmp[i]
            i += 1
        if len(cap) == 0:
            res.append(t)
            i += 1
        else:
            res.append(cap)

    # lemmatize words
    words = []
    for word in res:
        if not isinstance(word, str) or word == '':
            continue
        words.append(word)
    tokens = nltk.pos_tag(words)
    res = []
    for word, tag in tokens:
        wntag = get_pos(tag)
        if wntag is None:  # not supply tag in case of None
            word = lem.lemmatize(word)
        else:
            word = lem.lemmatize(word, pos=wntag)
        res.append(word)

    # segment concatenated words
    final_words = []
    for word in res:
        if not isinstance(word, str) or word == '':
            continue
        splited = func_name_segmentation(word)
        for w in splited:
            if not isinstance(w, str) or w == '':
                continue
            final_words.append(w)

    if len(final_words) == 0:
        return orig_name

    resulting_name =' '.join(final_words)
    if resulting_name.lower() != None:
        return resulting_name.lower()
    else:
        print (orig_name)
        return orig_name

if __name__ == '__main__':
    main()
