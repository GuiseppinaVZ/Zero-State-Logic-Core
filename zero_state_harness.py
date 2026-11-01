import os
import csv
import math
import sys
import time
import concurrent.futures
from openai import OpenAI

# ==========================================
# 1. THE PHYSICS ENGINE (VARIABLE ZERO CORE)
# ==========================================
def calculate_normalized_shannon_entropy(top_logprobs):
    if not top_logprobs: return 0.0
    raw_probabilities = [math.exp(token.logprob) for token in top_logprobs]
    total_p = sum(raw_probabilities)
    if total_p == 0: return 0.0
    normalized_p = [p / total_p for p in raw_probabilities]
    entropy = 0.0
    for p in normalized_p:
        if p > 0: entropy -= p * math.log2(p)
    return entropy

def check_epistemic_halt(response_chunk, entropy_threshold=2.0):
    try:
        if (response_chunk.choices and 
            response_chunk.choices[0].logprobs and 
            response_chunk.choices[0].logprobs.content):
            token_content = response_chunk.choices[0].logprobs.content[0]
            if hasattr(token_content, 'top_logprobs') and token_content.top_logprobs:
                current_entropy = calculate_normalized_shannon_entropy(token_content.top_logprobs)
                is_halt = current_entropy > entropy_threshold
                return is_halt, current_entropy
    except (AttributeError, IndexError):
        pass
    return False, 0.0

# ==========================================
# 2. DUAL-TRACK HARNESS (FULL ARMORED RUN)
# ==========================================
def run_dual_track_eval(input_csv, output_csv, entropy_threshold=2.0, max_prompts=None):
    main_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # mode='w' builds a fresh, clean file
    with open(input_csv, mode='r', encoding='utf-8-sig') as infile, \
         open(output_csv, mode='w', encoding='utf-8', newline='') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)

        # Write the headers
        writer.writerow([
            'Prompt_Index', 'Prompt', 'Track_A_Tokens_Naked', 'Track_A_Output',
            'Track_B_Tokens_LayerZero', 'Track_B_Halted', 'Track_B_Peak_Entropy_Bits',
            'Compute_Tokens_Saved', 'Savings_Percentage'
        ])
        outfile.flush()

        for idx, row in enumerate(reader, start=1):
            if max_prompts and idx > max_prompts: break

            prompt = row.get('Prompt') or row.get('Prompt_Text')
            print(f"\n[{idx}] Testing: {prompt[:50]}...")

            # TRACK A (Naked LLM)
            try:
                base_resp = main_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    stream=False, max_tokens=250, timeout=15.0
                )
                track_a_text = base_resp.choices[0].message.content or ""
                track_a_tokens = (base_resp.usage.completion_tokens 
                                  if (base_resp.usage and base_resp.usage.completion_tokens) 
                                  else len(track_a_text.split()))
            except Exception as e:
                print(f"   [!] Track A Network Error: {e}")
                track_a_text = f"API Error: {e}"
                track_a_tokens = 0

            # TRACK B (Thread Reaper with Disposable Client)
            def stream_track_b():
                b_text = ""
                b_tokens = 0
                b_halted = False
                m_entropy = 0.0
                try:
                    # DISPOSABLE CLIENT: Prevents connection pool starvation
                    disposable_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                    stream_resp = disposable_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        stream=True, logprobs=True, top_logprobs=5,
                        max_tokens=250, timeout=10.0
                    )
                    for chunk in stream_resp:
                        halt, entropy_val = check_epistemic_halt(chunk, entropy_threshold)
                        m_entropy = max(m_entropy, entropy_val)
                        if halt:
                            b_halted = True
                            b_text += " [EPISTEMIC HALT: LAYER ZERO TRIGGERED]"
                            break
                        if chunk.choices and chunk.choices[0].delta.content:
                            b_tokens += 1
                            b_text += chunk.choices[0].delta.content
                except Exception as e:
                    b_text = f"Stream Error: {e}"
                return b_text, b_tokens, b_halted, m_entropy

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(stream_track_b)
            try:
                track_b_text, track_b_tokens, track_b_halted, max_entropy = future.result(timeout=20.0)
                if track_b_halted:
                    print(f"   -> [HALT] Layer Zero cut stream at token {track_b_tokens}. Peak Entropy: {max_entropy:.3f} bits")
            except concurrent.futures.TimeoutError:
                print("   [!] THREAD REAPER: Stream deadlocked. Abandoning zombie thread.")
                track_b_text = "[STALL TIMEOUT: REAPER KILLED CONNECTION]"
                track_b_tokens = 0
                track_b_halted = False
                max_entropy = 0.0
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

            tokens_saved = max(0, track_a_tokens - track_b_tokens) if track_b_halted else 0
            savings_pct = round((tokens_saved / track_a_tokens * 100), 1) if (track_a_tokens > 0 and track_b_halted) else 0.0

            print(f"   Baseline: {track_a_tokens} tokens | Gate: {track_b_tokens} tokens | Saved: {savings_pct}% | Peak Entropy: {max_entropy:.3f} bits")

            writer.writerow([
                idx, prompt, track_a_tokens, track_a_text.replace("\n", " "),
                track_b_tokens, track_b_halted, round(max_entropy, 3),
                tokens_saved, f"{savings_pct}%"
            ])
            outfile.flush()
            
            time.sleep(1.0)

# ==========================================
# 3. EXECUTION
# ==========================================
if __name__ == "__main__":
    print("--- VARIABLE ZERO: THREAD REAPER HARNESS (FULL RUN) ---")

    target_csv = 'medical_eval.csv'
    output_csv = 'Comparative_Results_Medical.csv'

    run_dual_track_eval(target_csv, output_csv, entropy_threshold=2.0, max_prompts=100)

    print(f"\nEVALUATION COMPLETE. Comparative artifact saved to: {output_csv}")