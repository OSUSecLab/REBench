import json
import os
import sys
import sentencepiece as spm
import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
import argparse
import re
import copy


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
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str)
    parser.add_argument('--arch', type=str)
    parser.add_argument('--opt', type=str)
    parser.add_argument('--size', type=str, default=None)
    args = parser.parse_args()


    if args.size == None:
        outputfile = f'../output_result/{args.model}_{args.arch}_{args.opt}.json'
    else:
        outputfile = f'../diff_result/{args.model}_{args.size}_{args.arch}_{args.opt}.json'
    answerfile = f'../inputs/{args.arch}_{args.opt}_input.json'


    fp = open(answerfile, 'r')
    answer = json.load(fp)

    fp = open(outputfile, 'r')
    output = json.load(fp)

    c_type_cnt = 0
    c_type_correct = 0
    gt_total = 0
    total_cnt = 0
    total_accr = 0.0

    composite_cnt = 0
    total_type_cnt = 0
    for idx in answer:
        for value in answer[idx]["answer"]:
            if "TYPE" in value and "undefined" not in answer[idx]["answer"][value] and "None" not in answer[idx]["answer"][value]:
                val_value = value.replace('TYPE', 'VAR')
                if val_value in answer[idx]["answer"] and find_v(answer[idx]["answer"][val_value]) == False and len(answer[idx]["answer"][val_value]) != 0:
                    total_type_cnt += 1

    type_output = []
    for idx in output.keys():
        if len(output[idx]) == 0:
            continue
        lines = output[idx].split('\n')
        for line in lines:
            line = line.replace('`', '')
            line = line.replace('*', '')
            line = line.replace('-', '')
            line = line.replace(' ', '')

            if "Not specified" in line:
                continue

            if len(line.split(':')) < 2:
                continue

            target = line.split(':')[0]
            value = line.split(':')[1].split('<')[0]
            #.replace(" ", "")
            if len(value) == 0:
                continue

            if "TYPE" in target and target in answer[idx]["answer"] and "undefined" not in answer[idx]["answer"][target] and "None" not in answer[idx]["answer"][target]:
                val_value = target.replace('TYPE', 'VAR')
                if val_value in answer[idx]["answer"] and (find_v(answer[idx]["answer"][val_value]) == True or len(answer[idx]["answer"][val_value]) == 0):
                    continue
                flag = 0
                total_cnt += 1

                if value.replace(' ','') == answer[idx]["answer"][target].replace(' ', ''):
                    total_accr += 1


    type_tp = total_accr
    gt_type_count = total_type_cnt
    type_count = total_cnt
    type_precision = type_tp / type_count
    type_recall = type_tp / gt_type_count
    type_f1 = 2 * type_precision * type_recall / (type_precision + type_recall)

    if args.size == None:
        print (f'{args.model} {args.arch} {args.opt} {type_precision} {type_recall} {type_f1}')
    else:
        print (f'{args.model} {args.arch} {args.opt} {args.size} {type_precision} {type_recall} {type_f1}')

if __name__ == "__main__":
    main()
