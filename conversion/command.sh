#!/bin/bash

/home/junyeon/Developer/tool/ghidra_11.4.2_PUBLIC/support/analyzeHeadless /home/ lecture -import ./csplit -readOnly -postScript ./ghidra_preprocess_1.py
/home/junyeon/Developer/tool/ghidra_11.4.2_PUBLIC/support/analyzeHeadless /home/ lecture -import ./strip_csplit -readOnly -postScript ./ghidra_postprocess_1.py
/home/Developer/ida/idat -L"ida.log" -A -S"./ida_process.py" binary 
