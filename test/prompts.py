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
PROLOG_GENERATION_PROMPT = """
- Instructions:
- Given the insurance contract below, translate the document into valid Prolog rules so that I can run a Prolog query on the code regarding whether or not some claim is covered under the policy and receive the correct answer to the question.
- Please fully define all predicates and DO NOT define any facts, only rules that can be used to answer queries on this insurance contract.
- Assume that all dates/times in any query to this code (apart from the claimant's age) will be given RELATIVE to the effective date of the policy (i.e. there will never be a need to calculate the time elapsed between two dates). Take dates RELATIVE TO the effective date into account when writing this encoding.
- Assume that the agreement has been signed and the premium has been paid (on time). There is no need to encode rules or facts for these conditions.
- Return only Prolog code in your reply. No explanation is necessary.
- Ensure that:
1. The legal text is appropriately translated into correct Prolog rules.
2. The output does not redefine, misuse, or conflict with any built-in Prolog predicates.
3. If dynamic predicates are necessary, they are declared and managed correctly.
4. All predicates used in the generated Prolog code, including those referenced in the query, are fully defined and error-free to prevent issues like 'procedure does not exist.'
5. Logical relationships, conditions, and dependencies in the text are faithfully represented in the Prolog rules to ensure accurate query results.
6. The top-level predicate `is_claim_covered` is defined to check if a claim is covered under the policy, taking into account all relevant conditions and exclusions. 

And importantly: Include a comment around any Prolog code that explains what the code is doing, in plain English.
- Insurance contract: {contract_text}
"""

# --- Test Generation Prompt ------------------------------------------------------------

with open("query_generation_prompt.txt", "r", encoding='utf-8') as file:
    query_generation_prompt = file.read().strip()

# TEST_SUITE_GENERATION_PROMPT = """
# - I have given below:
# 1. A question about whether or not the policy defined in a given insurance contract applies in a particular situation
# 2. The text of the insurance contract
# 3. A Prolog encoding of the insurance contract
# - Encode the question into a Prolog query such that it can be run on the given Prolog encoding of the insurance contract, returning the correct answer to the question.
# - Assume that the agreement has been signed and the premium has been paid (on time). There is no need to encode rules or facts for these conditions.
# - Return only Prolog query in your reply. No explanation is necessary.

# - Ensure that:
# 1. The output does not redefine, misuse, or conflict with any built-in Prolog predicates.
# 2. If dynamic predicates are necessary, they are declared and managed correctly.
# 3. All predicates used in the generated Prolog code, including those referenced in the query, are fully defined and error-free to prevent issues like "procedure does not exist."
# 4. Logical relationships, conditions, and dependencies in the text are faithfully represented in the Prolog rules to ensure accurate query results.
# 5. No absolute dates/times (apart from the claimant's age) are encoded in your query. Only include dates/times RELATIVE to the effective date of the policy (again, except for age).
# 6. Set any facts/rules/parameters in the code such that ALL conditions (for the policy to apply) which are UNRELATED to the above query are satisfied.
# 7. Set any facts/rules/parameters in the code such that NO exclusions (which would prevent the policy from applying) which are UNRELATED to the above query are satisfied.

# And importantly: Include a comment at the top of the query that explains what the query is checking for, in plain English.
# - Insurance contract: {contract_text}
# """ 
# # This used to have: 
# # - Insurance contract Prolog encoding: {policy_encoding}
# # - Question:{query}
# # - Insurance contract: {text_content}

# TEST_SUITE_GENERATION_PROMPT = """
# You are given the text of an insurance contract. Your task is to generate a set of Prolog test cases that query this contract to determine whether or not certain scenarios are covered by the policy.

# Instructions:
# 1. Return exactly 3 to 5 individual Prolog test cases in the form:
#    test("label", prolog_goal).
# 2. Each test case must be a valid Prolog fact, and must include a string label as the first argument and a Prolog goal as the second.
# 3. Each test case should target a different aspect of the policy — e.g., coverage conditions, exclusions, age requirements, timing, etc.
# 4. DO NOT include any explanation or text. Only output Prolog code.
# 5. All test cases must use predicates that would exist in a reasonable encoding of the insurance contract.
# 6. Assume that all dates/times in any query to this code (apart from the claimant's age) will be given RELATIVE to the effective date of the policy (i.e. there will never be a need to calculate the time elapsed between two dates). Take dates RELATIVE TO the effective date into account when writing this encoding.
# 7. Assume that the agreement has been signed and the premium has been paid (on time). There is no need to encode rules or facts for these conditions.
# 8. If using multi-line compound goals, wrap them in parentheses, separated by commas.

# Insurance contract:
# {contract_text}
# """


TEST_SUITE_GENERATION_PROMPT = """
You are given the text of an insurance contract. Your task is to generate a set of Prolog test cases that query a hypothetical Prolog encoding of this contract to determine whether or not certain scenarios are covered by the policy.

Instructions:
1. Return exactly 3 to 5 individual Prolog test cases in the form:
   test("label", prolog_query).
2. Each test case must be a valid Prolog fact, and must include a string label as the first argument and a valid Prolog *query* as the second — NOT a rule or clause. Do NOT include the `:-` operator in any test.
3. Each test case should target a different aspect of the policy — e.g., coverage conditions, exclusions, age requirements, timing, etc.
4. DO NOT include any explanation or text. Only output Prolog code.
5. All test cases must use predicates that would exist in a reasonable encoding of the insurance contract.
6. All test cases must only query the public-facing predicate `is_claim_covered` to determine whether a claim is covered. Do not directly test helper or internal predicates like `is_policy_in_effect`, `policy_canceled`, or `condition_wellness_visit_satisfied`.
7. Each test case must represent a complete claim scenario and assert whether coverage applies.
8. If using compound goals (e.g., intermediate variable bindings), wrap them in parentheses, and separate them with commas.
9. DO NOT use `not`. Use `\+` for negation in Prolog.
10. Assume that all dates/times in any query to this code (apart from the claimant's age) will be given RELATIVE to the effective date of the policy (i.e., there will never be a need to calculate the time elapsed between two dates). Take dates RELATIVE TO the effective date into account when writing this encoding.
11. Assume that the agreement has been signed and the premium has been paid (on time). There is no need to encode rules or facts for these conditions.
12. All dates should be integer values representing days relative to the policy's effective date, e.g., `0` for the effective date, `1` for one day later, etc. Do not use absolute dates or words.
13. After each test case, include a line with exactly five hash symbols (#####) as a separator.
14. DO NOT define new predicates, rules, or clauses inside the test cases. Only use executable queries that can be run in isolation.
15. Ensure your tests use consistent predicate names and arities. Particularly; with is_claim_covered/x, ensure x is consistent across all tests.
16. Do NOT use keyword-style arguments like key=value. Prolog does not support this syntax. DO NOT use this style in your queries.

Insurance contract:
{contract_text}
"""



# # --- Vocabulary Mapping Prompt ----------------------------------------------------------

# with open("vocabulary_mapping_prompt.txt", "r", encoding='utf-8') as file:
#     vocabulary_mapping_prompt = file.read().strip()

# GLOBAL_MAPPING_PROMPT = """
# Instructions:
# 1.  Your task is to act as a vocabulary standardizer for a population of Prolog programs.
# 2.  You will receive a JSON object containing predicate signatures (e.g., "lessee/1") and the source comments that describe them.
# 3.  You may also receive a "prior_canonical_map" which contains decisions made from a previous batch.

# Your Goal:
# Create a single, consistent "canonical_map" that standardizes all synonymous predicates to a single "ground-truth" term.

# Reasoning Steps:
# 1.  Group predicates that represent the same real-world concept based on their names and descriptive comments. For example, 'insurer/1' and 'provider/1' are likely synonyms.
# 2.  For each group, elect one single predicate signature to be the "canonical" (ground-truth) form. A good choice is often the most descriptive or common term.
# 3.  If a "prior_canonical_map" is provided, you MUST adhere to its canonical choices for any predicates it already covers. Your task is to integrate the new predicates into the existing standard.
# 4.  Generate the final JSON map where every key is a predicate from the input and its value is the elected canonical predicate for its group.

# --- Prior Canonical Map (if any) ---
# {prior_map_json}

# --- Predicates to Analyze ---
# {predicates_json}

# --- Required JSON Output: Canonical Map ---
# """


DIAGNOSIS_PROMPT = """
You are an expert in both legal reasoning and logic programming.

Below is a Prolog program meant to encode an insurance contract. It has failed the following test cases.

Your job is to:
1. Identify the most likely reasons why this encoding failed the tests (e.g., missing rules, incorrect logic, misuse of predicates).
2. Offer targeted advice to improve the encoding logic for a next version, assuming the base instructions will still be followed. Your advice should not suggest changes to the test cases, but rather on the Prolog code itself.
3. Do not suggest simply hardcoding the answers to pass tests.
4. Focus on arity-related issues, as well as incorrect signatures and vocabulary mis-matches. Give specific examples of arity mismatches and vocabulary issues. These cause most of the issues in the tests.
5. If we're having an arity or vocabulary issue, you should explicitly give the signatures of the predicates that are causing issues to help guide the next version of the encoding.

### Contract Prolog Code:
```
{prolog_code}
```

### Failed Test Cases:
{failed_tests}

Return a short paragraph of explanation, followed by a bullet list of **actionable advice** to improve the next version.
"""