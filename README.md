# VariableZero: Zero-State Logic Harness

This repository contains a lightweight, empirical test slice of the VariableZero architecture. 

Current Large Language Models (LLMs) operate on unbounded probabilistic inference. When they lack structural variables, their probability matrix flattens, and they guess (hallucinate). This repository demonstrates a deterministic **Layer Zero Epistemic Deadbolt**. 

By continuously measuring the Top-5 Shannon Entropy of the token stream in real-time, the `zero_state_harness.py` engine mathematically detects when the model's confidence collapses. It enforces a strict **2.0-bit epistemic threshold**, severing the computational socket mid-stream before a probabilistic hallucination or security vulnerability can execute.

## The Stress Test Artifacts
This dual-track comparative harness was run against 199 high-liability prompts across two sectors:
* **Security (`Comparative_Results_Security.csv`):** 61.71% compute reduction. 53 adversarial attacks neutralized at the token level.
* **Medical (`Comparative_Results_Medical.csv`):** 82.71% compute reduction. 99 clinical hallucinations prevented.

## Execution Guide
The `zero_state_harness.py` file includes a "Thread Reaper" protocol that automatically kills deadlocked network sockets (preventing standard OpenAI streaming hangs). 

**The code is universal.** To switch the evaluation target between the Security and Medical datasets, modify Line 142 in `zero_state_harness.py`:

```python
# To test Security:
target_csv = 'security_eval.csv'
output_csv = 'Comparative_Results_Security.csv'

# To test Medical:
target_csv = 'medical_eval.csv'
output_csv = 'Comparative_Results_Medical.csv'