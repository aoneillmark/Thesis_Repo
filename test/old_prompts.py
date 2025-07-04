# --- Text Content ---
# This is from file `insurance_contract.txt`
with open("insurance_contract.txt", "r", encoding='utf-8') as file:
    text_content = file.read()

# --- Unguided Prolog Generation ---
with open("unguided_prolog_generation.txt", "r", encoding='utf-8') as file:
    unguided_prolog_generation = file.read().strip()


# --- Candidate solution ---------------------------------------------------------------

# --- Prompt Definition ---
# Create a clear and concise prompt for the AI.
PROLOG_GENERATION_PROMPT = f"""
- Instructions:
{unguided_prolog_generation}

- Insurance contract: {text_content}
"""

# --- Test Generation Prompt ------------------------------------------------------------

with open("query_generation_prompt.txt", "r", encoding='utf-8') as file:
    query_generation_prompt = file.read().strip()

TEST_SUITE_GENERATION_PROMPT = f"""
{query_generation_prompt}

- Question:{query}
- Insurance contract: {text_content}
- Insurance contract Prolog encoding: {policy_encoding}
"""

# --- Vocabulary Mapping Prompt ----------------------------------------------------------

with open("vocabulary_mapping_prompt.txt", "r", encoding='utf-8') as file:
    vocabulary_mapping_prompt = file.read().strip()

GLOBAL_MAPPING_PROMPT = f"""
Instructions:
1.  Your task is to act as a vocabulary standardizer for a population of Prolog programs.
2.  You will receive a JSON object containing predicate signatures (e.g., "lessee/1") and the source comments that describe them.
3.  You may also receive a "prior_canonical_map" which contains decisions made from a previous batch.

Your Goal:
Create a single, consistent "canonical_map" that standardizes all synonymous predicates to a single "ground-truth" term.

Reasoning Steps:
1.  Group predicates that represent the same real-world concept based on their names and descriptive comments. For example, 'insurer/1' and 'provider/1' are likely synonyms.
2.  For each group, elect one single predicate signature to be the "canonical" (ground-truth) form. A good choice is often the most descriptive or common term.
3.  If a "prior_canonical_map" is provided, you MUST adhere to its canonical choices for any predicates it already covers. Your task is to integrate the new predicates into the existing standard.
4.  Generate the final JSON map where every key is a predicate from the input and its value is the elected canonical predicate for its group.

--- Prior Canonical Map (if any) ---
{prior_map_json}

--- Predicates to Analyze ---
{predicates_json}

--- Required JSON Output: Canonical Map ---
"""