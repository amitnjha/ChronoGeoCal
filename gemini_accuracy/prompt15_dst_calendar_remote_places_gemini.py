import json

def parse_timestamp(ts_str):
    """
    Parses a timestamp string 'YYYY-MM-DD HH:MM:SS' into (date, time).
    """
    if not ts_str or not isinstance(ts_str, str):
        return None, None
    try:
        parts = ts_str.strip().split(' ')
        if len(parts) == 2:
            return parts[0], parts[1]
        return None, None
    except Exception:
        return None, None

def evaluate_dst_responses(input_file, output_file):
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        evaluation_results = []

        for i, entry in enumerate(data):
            model_resp = entry.get('response', '')
            targets = entry.get('target_scores', {})
            
            # Identify the correct answer (score 1.0)
            correct_resp = next((k for k, v in targets.items() if v == 1.0), None)
            
            # Exact match check
            exact_match = (model_resp == correct_resp)
            
            # Partial credit logic (Date vs Time)
            m_date, m_time = parse_timestamp(model_resp)
            c_date, c_time = parse_timestamp(correct_resp)
            
            date_ok = (m_date == c_date) if (m_date and c_date) else False
            time_ok = (m_time == c_time) if (m_time and c_time) else False
            
            score = 1.0 if exact_match else (0.5 if date_ok else 0.0) + (0.5 if time_ok else 0.0)
            
            evaluation_results.append({
                "index": i + 1,
                "model_response": model_resp,
                "correct_response": correct_resp,
                "is_exact_match": exact_match,
                "date_match": date_ok,
                "time_match": time_ok,
                "final_score": score
            })

        with open(output_file, 'w') as f:
            json.dump(evaluation_results, f, indent=4)
            
        print(f"Evaluation complete. Results saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    evaluate_dst_responses(
        'prompt15_dst_calendar_remote_places_gemini.json', 
        'prompt15_dst_calendar_remote_places_gemini_accuracy.json'
    )