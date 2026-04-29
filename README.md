# REBench

## Experiment Setup
Please follow the command to prepare dependency.
```
conda create -n rebench python=3.12
conda activate rebench
pip install -r requirements.txt
```

## Data Generation
REBench can be generated via two decmopilers, ghidra and IDA Pro. We utilized Ghidra 11.4.2 and IDA 7.6.
Ghidra decompiler requires preprocessing.
```
/path/to/ghidra/support/analyzeHeadless /proj-dir /proj-name -import ./binary -readOnly -postScript ./ghidra_preprocess_1.py
/path/to/ghidra/support/analyzeHeadless /proj-dir /proj-name -import ./strip_binary -readOnly -postScript ./ghidra_postprocess_1.py
```
The binary should contain symbols and the second script should execute with stripped binaries.

IDA does not need preprocessing.
```
/path/to/ida/idat -L"log" -A -S"./ida_process.py" binary
```


## Model Execution
We provide finetuning and running scripts for CodeLlama.

```
python finetune_codellma.py
python codellama_script.py --arch arch --opt opt
```

## Result Evaluation
To evaluate the name recovery, please follow the execution steps from the name_eval directory.
```
python parse.py codellama x64 O0
python evaluation.py --evaluation-input evaluation_input_codellama_x64_O0_func.txt
python evaluation.py --evaluation-input evaluation_input_codellama_x64_O0_var.txt
```

To evaluate the type inference, please follow the execution step from the type_eval directory.
```
python type_evaluation.py --model model_name --arch arch --opt opt
```

## Dataset
You can find binaries and generated decompiled code from the following link.

