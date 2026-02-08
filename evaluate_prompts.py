import sys
import os
import json
import requests
from evaluation import call_llm
from global_config import MAX_COUNT,PLACES_FILE, PROMPT_DIR, PROMPT_WITH_INFER, PROMPT_WITH_ACCURACY

endpoint_dict = {
        "CohereLabs/aya-expanse-32b": "",
        "openai/gpt-oss-120b": "",
        "meta-llama/Llama-3.3-70B-Instruct": "",
        "Qwen/Qwen2.5-72B-Instruct": "",
        "Qwen/Qwen2.5-7B-Instruct": "",
        "Qwen/Qwen2.5-14B-Instruct": "",
        "CohereLabs/aya-23-8B": "",
        "google/gemma-3-12b-it": "",
        "google/gemma-3-27b-it": "",
        "mistralai/Mistral-Small-24B-Instruct-2501": "",
        "mistralai/Mistral-7B-Instruct-v0.3": ""
        }

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("evaluate_prompts.py <MODEL_NAME> <PROMPT_JSON_FILE_NAME>")
        print("where MODEL_NAME can be one of the following -- CohereLabs/aya-expanse-32b, openai/gpt-oss-120b, meta-llama/Llama-3.3-70B-Instruct, Qwen/Qwen2.5-72B-Instruct")
    else:
        if sys.argv[1] in list(endpoint_dict.keys()):
            MODEL_NAME = sys.argv[1]
            endpoint = endpoint_dict.get(MODEL_NAME)
            file_name = sys.argv[2]
            print("Checking prompts from file ", file_name);
            if os.path.exists(file_name):
                data = []
                outDat = []
                i = 0
                with open(file_name) as f:
                    data = json.load(f)
                    #print("Ready to roll with, ", len(data), " prompts")
                    for dat in data:
                        if i <= MAX_COUNT:
                            print("Prompting ", MODEL_NAME, " with ", dat['input'], " ## ", i)
                            prompt_dict ={
                                "model": MODEL_NAME,
                                "messages": [
                                {
                                    "role": "system",
                                    "content": "You are supposed to perform reasoning on various calendars"
                                },
                                {
                                    "role": "user",
                                    "content": dat['input']
                                }
                            ]
                            }
                            prompt_string = json.dumps(prompt_dict, ensure_ascii = False)
                            headers = {"Content-Type": "application/json; charset=utf-8","Accept": "application/json"}

                            #make the api call
                            #print(prompt_string)
                            #response = requests.post(endpoint, json = prompt_string, headers = headers )
                            response = call_llm(api_url =  endpoint, model = MODEL_NAME, system_prompt = "", user_prompt = dat['input'] )
                            print(response)
                            dat['response'] = response
                            dat['isModelResponseCorrect'] = 'TBD'

                            #print(response.status_code)
                            #print(response.text)
                            #print(response.json())
                            i+=1
                            outDat.append(dat)
            else:
                    print("ERROR: File path does not exist", file_name)
            #print(json.dumps(outDat, ensure_ascii = False,indent = 4))
            file_name_out =  MODEL_NAME + '_' + file_name[0 : file_name.index('.')] + '.json'
            file_name_out = file_name_out.replace('/','_')
            with open(PROMPT_WITH_INFER + "/" + file_name_out, "w") as file:
                file.write(json.dumps(outDat, ensure_ascii = False,indent = 4))
        else:
                print("Please provide a valid model name , ['CohereLabs/aya-expanse-32b', 'openai/gpt-oss-120b', 'meta-llama/Llama-3.3-70B-Instruct','Qwen/Qwen2.5-72B-Instruct']")
    

