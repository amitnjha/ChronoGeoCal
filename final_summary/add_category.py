
import pandas as pd

#df = pd.read_csv("regular_prompts.csv")
df = pd.read_csv("prompts_with_cot_without_llama.csv")

class_dict = {
 "prompt2": "Time",
 "prompt3": "Time",
 "prompt4": "Time",
 "prompt5": "Time",
 "prompt6": "Time",
 "prompt7": "Time",
 "prompt9": "Time",
 "prompt10": "Time",
 "prompt11": "Time",
 "prompt13": "Time",
 "prompt15": "Time",
 "prompt16": "Calendar",
 "prompt17": "Calendar",
 "prompt18": "Calendar",
 "prompt19": "Calendar",
 "prompt20": "Calendar",
 "prompt21": "Calendar",
 "prompt22": "Calendar",
 "prompt24": "Time"
}

# df_classes_for_prmopts = pd.read_csv("classes.csv")

# print(df_classes_for_prmopts.head())
# mapping = df_classes_for_prmopts.set_index('prompt_num')['Category']

print(class_dict.get("prompt10", "Unknown"))

df['Category'] = df['prompt_num'].map(lambda x: class_dict.get(x, 'Unknown'))

df.to_csv("prompts_with_cot_without_llama_category.csv", index=False)

print(df.head(20))
