#!/bin/bash

/path/to/ghidra/support/analyzeHeadless /home/ llm -import ./cat -readOnly -postScript ./ghidra_preprocess_1.py
/path/to/ghidra/support/analyzeHeadless /home/ llm -import ./split_cat -readOnly -postScript ./ghidra_postprocess_1.py
/path/to/ida/idat -L"ida.log" -A -S"./ida_process.py" binary 
