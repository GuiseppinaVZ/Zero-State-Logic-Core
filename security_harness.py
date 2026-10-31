import os
import csv
import time
from openai import OpenAI
# 1. SECURE INFRASTRUCTURE
with open("api.key", "r") as file:
    secret_key = file.read().strip()
client = OpenAI(api_key=secret_key)
    secret_key = file.read().strip()

client = OpenAI(api_key=secret_key)

# 2. THE VARIABLE ZERO BLACK BOX (SECURITY GATE)
def variable_zero_gate(prompt_text):
    text = prompt_text.lower()
    
    # Structural Schema Rules: Identify adversarial injection vectors
    injection_indicators = [
        "ignore all previous", "disregard", "forget everything", "deprecated",
        "system prompt", "admin privileges", "override", "root access",
        "developer mode", "no filters", "unrestricted", "jailbreak",
        "sudo user", "base64", "rot13", "decode", "payload"
    ]
    
    # Rule 1: If the text contains known adversarial override syntax, HALT.
    for indicator in injection_indicators:
        if indicator in text:
            return True
            
    # If it passes all structural checks, allow computation.
    return False 

# 3. THE PROBABILISTIC BASELINE
def fetch_naked_llm_response(prompt_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7 
        )
        answer = response.choices[0].message.content.strip()
        tokens_burned = response.usage.total_tokens
        answer_clean = answer.replace('\n', ' ').replace(',', ';')
        return f"{answer_clean}", tokens_burned
    except Exception as e:
        return f"API ERROR: {str(e)}", 0

# 4. THE EXECUTION LOOP
def run_crash_test(input_filename, output_filename):
    print(f"INITIATING EVALUATION: {input_filename}...")
    
    with open(input_filename, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        
        with open(output_filename, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["Prompt_ID", "Raw_Prompt", "Variable_Zero_Output", "Naked_LLM_Output", "Tokens_Burned_By_LLM", "Thermodynamic_Tokens_Saved"])
            
            for row in reader:
                prompt_id = row['Prompt_ID']
                prompt_text = row['Prompt_Text']
                print(f"Testing Prompt {prompt_id}/100...")
                
                is_halted = variable_zero_gate(prompt_text)
                
                if is_halted:
                    vz_result = "[ EPISTEMIC HALT ] - Malicious Syntax Intercepted."
                    tokens_saved = 0 
                else:
                    vz_result = "[ PASSED ]"
                    
                llm_response, naked_tokens = fetch_naked_llm_response(prompt_text)
                
                if is_halted:
                    tokens_saved = naked_tokens 
                else:
                    tokens_saved = 0
                
                writer.writerow([prompt_id, prompt_text, vz_result, llm_response, naked_tokens, tokens_saved])
                time.sleep(0.5) 

    print(f"EVALUATION COMPLETE. Artifact saved to: {output_filename}")

# 5. INITIATE PROTOCOL (SECURITY ONLY)
if __name__ == "__main__":
    run_crash_test("security_eval.csv", "Eval_Results_Security.csv")