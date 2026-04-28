import os
import sys

import fire
import torch
import transformers
from peft import PeftModel
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer, CodeLlamaTokenizer

from utils.callbacks import Iteratorize, Stream
from utils.prompter import Prompter

import json


code_type = 'decompile'
model_type = 'CodeLlama-34b-Instruct'

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:  # noqa: E722
    pass


def main(
    load_8bit: bool = False,
    base_model: str = "",
    #lora_weights: str = "tloen/alpaca-lora-7b",
    lora_weights: str = "",
    prompt_template: str = "codellama",  # The prompt template to use, will default to alpaca.
    server_name: str = "0.0.0.0",  # Allows to listen on all interfaces by providing '0.
    share_gradio: bool = False,
    arch: str = "",
    opt: str = "",
    decomp: str=""
):
    base_model = base_model or os.environ.get("BASE_MODEL", "")
    assert (
        base_model
    ), "Please specify a --base_model, e.g. --base_model='huggyllama/llama-7b'"

    prompter = Prompter(prompt_template)
    #tokenizer = AutoTokenizer.from_pretrained(base_model)
    #tokenizer = LlamaTokenizer.from_pretrained(base_model)
    tokenizer = CodeLlamaTokenizer.from_pretrained(base_model)
    #tokenizer = CodeLlamaTokenizer.from_pretrained("codellama/CodeLlama-13b-Instruct-hf")

    if device == "cuda":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            load_in_8bit=load_8bit,
            torch_dtype=torch.float16,
            device_map="auto",
            cache_dir='models/',
        )

        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            torch_dtype=torch.float16,
        )
        #model = model.merge_and_unload()

    # unwind broken decapoda-research config
    model.config.pad_token_id = tokenizer.pad_token_id = 0  # unk
    model.config.bos_token_id = 1
    model.config.eos_token_id = 2
    # print(repr(tokenizer.pad_token)) ## ''
    # print(repr(tokenizer.bos_token)) ## ''
    # print(repr(tokenizer.eos_token)) ## ''

    if not load_8bit:
        model.half()  # seems to fix bugs for some users.

    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    def evaluate(
        instructionList,
        inputList=None,
        temperature=0.1,
        top_p=0.75,
        top_k=40,
        num_beams=1,
        #max_new_tokens=256,
        max_new_tokens=1024,
        stream_output=False,
        **kwargs,
    ):
        # if inputList is None:
        #     prompt = [prompter.generate_prompt(instruction, None) for instruction in instructionList]
        # else:
        #     prompt = [prompter.generate_prompt(instruction, input) for instruction, input in zip(instructionList, inputList)]

        # print(prompt)
        # inputs = tokenizer.batch_encode_plus(prompt, return_tensors="pt", padding=True, truncation=True)

        prompt = prompter.generate_prompt(instructionList, inputList)
        #prompt = f"<s>[INST] <<SYS>>\\n{instructionList}\\n<</SYS>>\\n\\n{inputList}[/INST]"
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            num_beams=num_beams,
            **kwargs,
        )

        generate_params = {
            "input_ids": input_ids,
            "generation_config": generation_config,
            "return_dict_in_generate": True,
            "output_scores": True,
            "max_new_tokens": max_new_tokens,
        }

        # Without streaming
        with torch.no_grad():
            if len(input_ids[0]) < 1024:
                generation_output = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    pad_token_id=tokenizer.pad_token_id,
                    generation_config=generation_config,
                    repetition_penalty=1.1,
                    return_dict_in_generate=True,
                    output_scores=True,
                    max_new_tokens=max_new_tokens,
                )
                s = generation_output.sequences[0]
                output = tokenizer.decode(s)
                # s = generation_output.sequences
                # output = tokenizer.batch_decode(s, skip_special_tokens=True)
                # return output # codellama
                return prompter.get_response(output) # llama2
            else:
                return ""


    fileinput = "inputs/" + arch + "_" + opt + "_input.json"
    fp = open(fileinput, 'r')
    funcs = json.load(fp)

    output = {}
    for k, v in funcs.items():
        print (k)
        instruction =  "Let's assume you are a programmer. A decompiled C function is given, and the name of the function and the types and names of variables are changed to FUNC, VAR, and TYPE.          Understand the function and infer original names of replacements without explanation. Output the result format as follows. e.g., \"FUNC1: printf\", \"VAR1: count\", \"VAR2: index\", \"TYPE1: int\",       \"TYPE2: char\"."
        inputs = "Now here is a decompiled code of a function: \n" + v["funcbody"] + "Please provide the original name of " + ", ".join(v["answer"].keys()) + "?"
        res = evaluate(instruction, inputs)
        output[k] = res

    with open(f"finetune_output/codellama_{arch}_{opt}.json", 'w') as fout:
        json.dump(output, fout, indent=2)



if __name__ == "__main__":
    fire.Fire(main)
