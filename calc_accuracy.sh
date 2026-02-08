#!/bin/zsh

#echo 'Calculating accuracy'

#files=$(ls -1 *output.json)

PROMPT_WITH_ACCURACY="prompts_with_accuracy_cot"

#files=("$PROMPT_WITH_ACCURACY/meta-llama_Llama-3.3-70B-Instruct_prompts_prompt22_shipping_businessdays_remote_places_output.json")

#for file in "${files[@]}";
echo "prompt,Total Count,False Count,True Count,Accuracy,sample"
for file in $PROMPT_WITH_ACCURACY/*; do
    if [ -e "$file" ]; then;
        falsecount=$(cat $file | grep '"isModelResponseCorrect": false' | wc -l)
        truecount=$(cat $file | grep '"isModelResponseCorrect": true' | wc -l)
        totalcount=$(cat $file | grep '"isModelResponseCorrect"' | wc -l)
        accuracy="$((truecount*1.0*100/totalcount))%"
        sample=$(cat $file | jq '.[0].input')
        #accuracy=$($truecount*1.0/$totalcount)
        echo "$file,$totalcount,$falsecount,$truecount,$accuracy,$sample"
    fi
done

#totalcount=$(cat $file | grep '"isModelResponseCorrect": false' | wc -l)
#totalcount="$(cat $file | grep '"isModelResponseCorrect": false' | wc -l )"
#echo "$totalcount"    


