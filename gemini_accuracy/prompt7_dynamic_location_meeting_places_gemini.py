import json

def parse_response_string(resp_str):
    """
    Parses a response string in the format:
    'actual: YYYY-MM-DD HH:MI, misunderstood: YYYY-MM-DD HH:MI'
    Returns a tuple of (actual, misunderstood) or (None, None) if parsing fails.
    """
    if not resp_str or not isinstance(resp_str, str):
        return None, None
    try:
        # Splitting by comma to separate the two parts
        parts = resp_str.split(',')
        # Cleaning up 'actual:' and 'misunderstood:' prefixes
        actual_part = parts[0].replace('actual:', '').strip()
        misunderstood_part = parts[1].replace('misunderstood:', '').strip()
        return actual_part, misunderstood_part
    except (IndexError, AttributeError):
        return None, None

def evaluate_responses(input_file, output_file):
    try:
        # Load the data from the local JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        results_table = []

        for index, entry in enumerate(data):
            model_response = entry.get('response', '')
            target_scores = entry.get('target_scores', {})
            
            # Find the ground truth (the key with score 1.0)
            correct_response = next((k for k, v in target_scores.items() if v == 1.0), None)
            
            # Parse both the model and correct responses into parts
            m_actual, m_misunderstood = parse_response_string(model_response)
            c_actual, c_misunderstood = parse_response_string(correct_response)
            
            # 1. Full Match Check
            is_exact_match = (model_response == correct_response)
            
            # 2. Partial Credit Logic (0.5 for each correct part)
            actual_correct = (m_actual == c_actual) if (m_actual and c_actual) else False
            misunderstood_correct = (m_misunderstood == c_misunderstood) if (m_misunderstood and c_misunderstood) else False
            
            score = 0.0
            if is_exact_match:
                score = 1.0
            else:
                if actual_correct: score += 0.5
                if misunderstood_correct: score += 0.5

            # Store the evaluation in a dictionary
            results_table.append({
                "id": index + 1,
                "input_snippet": entry.get("input", "")[:50] + "...",
                "model_response": model_response,
                "correct_response": correct_response,
                "is_model_correct_bool": is_exact_match,
                "actual_time_correct": actual_correct,
                "misunderstood_time_correct": misunderstood_correct,
                "partial_credit_score": score
            })

        # Save the evaluation table to a new JSON file
        with open(output_file, 'w') as f:
            json.dump(results_table, f, indent=4)
            
        print(f"Successfully processed {len(results_table)} entries.")
        print(f"Results saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode the JSON file. Ensure it is formatted correctly.")

if __name__ == "__main__":
    # Local file names
    INPUT_FILENAME = 'prompt7_dynamic_location_meeting_places_gemini.json'
    OUTPUT_FILENAME = 'accuracy_evaluation_table.json'
    
    evaluate_responses(INPUT_FILENAME, OUTPUT_FILENAME)
