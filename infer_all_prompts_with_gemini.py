import sys
import os
import json
from google import genai

# The client will automatically look for the GEMINI_API_KEY environment variable.
# Or you can pass it explicitly: client = genai.Client(api_key="YOUR_API_KEY")
client = genai.Client()

for model in client.models.list():
    print(model.name)
    
"""
response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents="Explain the Raft consensus algorithm in one sentence."
)
"""

limit = int(sys.argv[1])

print("I will infer ", limit, " prompts");

for prompt_file in os.listdir('prompts'):
    #print(prompt_file)
    with open('prompts/'+prompt_file, 'r') as file:
        print('processing file ', file)
        content =  file.read()
        prompt_array = json.loads(content)
        # print(len(prompt_array))
        running_idx = 0
        gemini_response_list = []
        for prompt in prompt_array:
            #infer gemini and save data in a list
            print(running_idx , prompt)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt['input']
                )
            prompt["response"] = response.text
            prompt["isModelResponseCorrect"] = "TBD"
            gemini_response_list.append(prompt)
            #print(response.text)
            #print(prompt)
            running_idx+=1
            if running_idx >= limit or running_idx == len(prompt_array)-1:
                #write list to file and reset running index
                output_file = prompt_file.split('.')[0] + '_gemini' + '.json'
                with open('gemini_infer/'+output_file, 'w', encoding='utf-8') as f:
                    json.dump(gemini_response_list, f, indent=4)
                gemini_response_list = []
                running_idx = 0
                break
                
        

