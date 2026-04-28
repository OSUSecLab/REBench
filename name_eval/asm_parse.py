import os
import sys
import sentencepiece as spm
import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet

import json
import copy

sp = spm.SentencePieceProcessor()
sp.load('./segmentation_model/segmentation.model')
lem = WordNetLemmatizer()


def main():
    outputname = '../asm_result/' + str(sys.argv[1]) + '_' + str(sys.argv[2]) + '_' + str(sys.argv[3]) + '.json'
    answername = '../inputs/' + str(sys.argv[2]) + '_' + str(sys.argv[3]) + '_input.json'

    fp = open(answername, 'r')
    answer_gt = json.load(fp)

    fp = open(outputname, 'r')
    output_gt = json.load(fp)

    gt_func_cnt = 0

    for i in answer_gt:
        if i not in output_gt or len(output_gt[i]) == 0:
            continue
        answers = answer_gt[i]["answer"]
        #for answer in answers:
        if "FUNC1" in answers:
            gt_func_cnt += 1

    func_total = 0
    temp = {}
    all_output = []
    for idx in output_gt.keys():
        answer = {}
        if len(output_gt[idx]) == 0:
            continue
        lines = output_gt[idx].split('\n')

        for line in lines:
            if len(line.split(':')) != 2:
                continue

            if len(line.split()) != 2:
                continue

            target = line.split(':')[0]
            value = line.split(':')[1].split('<')[0].replace(" ", "")
            if len(value) == 0:
                continue


            if "FUNC" in target:
                func_total += 1
                answer[target] = value
                result = ""
                result += func_name_preprocessing(value)
                result += ","
                result += func_name_preprocessing(answer_gt[idx]["answer"]["FUNC1"])
                result += ",["
                prob = [1.0000]*len(func_name_preprocessing(answer_gt[idx]["answer"]["FUNC1"]).split())
                result += " ".join(str(e) for e in prob)
                result += "]\n"
                all_output.append(result)
                break




    fp = open('evaluation_input_' + str(sys.argv[1]) + '_' + str(sys.argv[2]) + '_' + str(sys.argv[3]) + '_all.txt', 'w')
    for line in all_output:
        fp.write(line)
    fp.close()


    print (f'{sys.argv[1]} {sys.argv[2]} {sys.argv[3]} {gt_func_cnt} {func_total}')


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
