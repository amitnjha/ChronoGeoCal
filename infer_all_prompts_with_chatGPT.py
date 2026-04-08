import sys
import os
import json
from openai import OpenAI

# Initialize OpenAI client
# Requires environment variable: OPENAI_API_KEY
client = OpenAI()

# Read limit (number of prompts to process per file) from command line
limit = int(sys.argv[1])

print("I will infer ", limit, " prompts")

# Loop through all files inside the 'prompts' directory
for prompt_file in os.listdir('prompts'):

    # Open and read each prompt file (assumes JSON format)
    with open('prompts/' + prompt_file, 'r') as file:
        print('processing file ', file)

        content = file.read()
        prompt_array = json.loads(content)  # Convert JSON string → Python list

        running_idx = 0
        gpt_response_list = []

        # Iterate through each prompt in the file
        for prompt in prompt_array:
            print(running_idx, prompt)

            # Send prompt to ChatGPT (OpenAI API)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-efficient model
                messages=[
                    {"role": "user", "content": prompt['input']}
                ]
            )

            # Extract model response text
            prompt["response"] = response.choices[0].message.content

            # Placeholder for evaluation (to be filled later)
            prompt["isModelResponseCorrect"] = "TBD"

            # Add updated prompt to results list
            gpt_response_list.append(prompt)

            running_idx += 1

            # Save results when:
            # 1. Reached limit
            # 2. Reached end of prompt list
            if running_idx >= limit or running_idx == len(prompt_array) - 1:

                # Create output filename (same name + _gpt suffix)
                output_file = prompt_file.split('.')[0] + '_gpt' + '.json'

                # Write results to output directory
                with open('gpt_infer/' + output_file, 'w', encoding='utf-8') as f:
                    json.dump(gpt_response_list, f, indent=4)

                # Reset for next batch
                gpt_response_list = []
                running_idx = 0

                # Exit loop after writing batch
                break