# --- Text Content ---
# This is from file `insurance_contract.txt`
# with open("insurance_contract.txt", "r", encoding='utf-8') as file:
#     text_content = file.read()

# # --- Unguided Prolog Generation ---
# with open("unguided_prolog_generation.txt", "r", encoding='utf-8') as file:
#     unguided_prolog_generation = file.read().strip()


# --- Candidate solution ---------------------------------------------------------------

# --- Prompt Definition ---
# Create a clear and concise prompt for the AI.
PROLOG_GENERATION_PROMPT = """
- Insurance contract: {contract_text}

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
7. Include a comment around any Prolog code that explains what the code is doing, in plain English.
"""

# --- Test Generation Prompt ------------------------------------------------------------

# with open("query_generation_prompt.txt", "r", encoding='utf-8') as file:
#     query_generation_prompt = file.read().strip()


TEST_SUITE_GENERATION_PROMPT = """
You are given the text of an insurance contract.
Your task is to generate a set of Prolog test cases that query a hypothetical Prolog encoding of this contract to determine whether or not certain scenarios are covered by the policy.

Insurance contract:
{contract_text}

Instructions:
1. Return exactly 3 to 5 individual Prolog test cases in the form:
   test("label", prolog_query).
**Immediately above each test case, add a single-line Prolog comment (starting
   with `%`) that concisely explains what each argument of the query means.**
   Example:
     % Args: Name, DateOfBirth, Gender
     test("basic_cover", is_mcdonalds_customer('Johnny Appleseed', 01011973, Male)).
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
"""





TEST_REPAIR_PROMPT = """
You are fixing ONE Prolog query so that its predicate names & arities match all programs shown below (keep query intent).
----- FAILING PROGRAMS -----
{prog_snips}

----- Failing Query -----
{failing_query}

Produce ONLY the corrected test query.
Extra instructions:
1. Return your query in the form:
   test("label", prolog_query).
**Immediately above the test case, add a single-line Prolog comment (starting
   with `%`) that concisely explains what each argument of the query means.**
   Example:
     % Args: Name, DateOfBirth, Gender
     test("basic_cover", is_mcdonalds_customer("Johnny Appleseed", 01011973, Male)).
2. Each test case must be a valid Prolog fact, and must include a string label as the first argument and a valid Prolog *query* as the second — NOT a rule or clause. Do NOT include the `:-` operator in any test.
3. DO NOT include any explanation or text. Only output Prolog code.
4. The test case must only query the public-facing predicate `is_claim_covered` to determine whether a claim is covered. Do not directly test helper or internal predicates.
5. If using compound goals (e.g., intermediate variable bindings), wrap them in parentheses, and separate them with commas.
6. DO NOT use `not`. Use `\+` for negation in Prolog.
7. DO NOT define new predicates, rules, or clauses inside the test cases. Only use executable queries that can be run in isolation.
8. Do NOT use keyword-style arguments like key=value. Prolog does not support this syntax. DO NOT use this style in your queries.
"""



REFERENCE_BLOCK = """
You have already produced some *valid* test cases earlier:

{existing_tests}

When you create NEW tests, **reuse the same public predicate name
(`is_claim_covered`) and keep its arity identical**.  Do *not* copy the
old tests verbatim; generate fresh scenarios, but stay consistent with
the signature you see above.
"""



TEST_GENERATION_PROMPT = """
You are given the text of an insurance contract.
Your task is to generate a single Prolog test case that queries a hypothetical Prolog encoding of this contract to determine whether or not a specific scenario is covered by the policy.

Insurance contract:
{contract_text}

Instructions:
1. Return exactly 1 Prolog test case in the form:
   test("label", prolog_query).
**Immediately above the test case, add a single-line Prolog comment (starting
   with `%`) that concisely explains what each argument of the query means.**
   Example:
     % Args: Name, DateOfBirth, Gender
     test("basic_cover", is_mcdonalds_customer('Johnny Appleseed', 01011973, Male)).
2. The test case must be a valid Prolog fact, and must include a string label as the first argument and a valid Prolog *query* as the second — NOT a rule or clause. Do NOT include the `:-` operator in the test.
3. The test case should target a specific aspect of the policy — e.g., coverage conditions, exclusions, age requirements, timing, etc.
4. DO NOT include any explanation or text. Only output Prolog code.
5. The test case must use predicates that would exist in a reasonable encoding of the insurance contract.
6. The test case must only query the public-facing predicate `is_claim_covered` to determine whether a claim is covered. Do not directly test helper or internal predicates like `is_policy_in_effect`, `policy_canceled`, or `condition_wellness_visit_satisfied`.
7. The test case must represent a complete claim scenario and assert whether coverage applies.
8. If using compound goals (e.g., intermediate variable bindings), wrap them in parentheses, and separate them with commas.
9. DO NOT use `not`. Use `\+` for negation in Prolog.
10. Assume that all dates/times in any query to this code (apart from the claimant's age) will be given RELATIVE to the effective date of the policy (i.e., there will never be a need to calculate the time elapsed between two dates). Take dates RELATIVE TO the effective date into account when writing this encoding.
11. Assume that the agreement has been signed and the premium has been paid (on time). There is no need to encode rules or facts for these conditions.
12. All dates should be integer values representing days relative to the policy's effective date, e.g., `0` for the effective date, `1` for one day later, etc. Do not use absolute dates or words.
13. DO NOT define new predicates, rules, or clauses inside the test case. Only use an executable query that can be run in isolation.
14. Ensure your test uses consistent predicate names and arities with is_claim_covered/x.
15. Do NOT use keyword-style arguments like key=value. Prolog does not support this syntax. DO NOT use this style in your query.

We have a number of test cases that have already been run against the Prolog code, some of which have passed and some of which have failed.
Your task is to generate a new test case that is consistent with the existing tests (function signature and arity), but which explores a different scenario.
Identify potential problems or edge cases in the program. Focus on gaps in logic or unusual scenarios. It's best if you can think of a unique scenario that has not been tested before, which is consistent with the rules of the contract text.

Here's the best program so far:
{program}

Here are the tests that the best program has failed:
{failing}

Here are the tests that the best program has passed:
{passing}

"""



# --- Diagnosis Prompt ------------------------------------------------------------------
# This prompt is used to diagnose issues in the Prolog code based on failed test cases.

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

# ----------------------------------------------------------------------------------------
# Genetic Operators Prompts --------------------------------------------------------------
# ----------------------------------------------------------------------------------------

PROGRAM_CROSSOVER_PROMPT = """
You are merging **two** independently written Prolog encodings of the same
insurance contract into a single, higher-quality child program.

================  CONTEXT  ================
--- INSURANCE CONTRACT (excerpt) ---
{contract_text}

--- PARENT A ---
{parent_a}

--- PARENT B ---
{parent_b}
===========================================

TASK
----
1. Combine the strengths of both parents: keep logically correct rules,
   deduplicate or reconcile conflicting clauses, and choose the clearer
   predicate names when synonyms occur.
2. *Do not* introduce any ground facts - **rules only**.
3. Keep the public interface predicate `is_claim_covered/N` exactly the same
   arity it has in the parents.  All other helper predicates may be renamed if
   necessary for consistency, but make sure every reference is updated.
4. Add concise English comments (`% …`) explaining each rule block.
5. Return **only** valid Prolog code - no Markdown, no explanation text.
"""



# † Variables injected: {contract_text}, {program}
PROGRAM_MUTATION_PROMPT = """
You are improving a Prolog encoding of the insurance contract shown below.
Make edits that fix bugs, add missing edge-cases, or
simplify logic, while preserving the external interface (preserve is_claim_covered/N).

================  CONTEXT  ================
--- INSURANCE CONTRACT (excerpt) ---
{contract_text}

--- CURRENT PROGRAM ---
{program}
===========================================

REQUIREMENTS
------------
• Do **NOT** add ground facts; rules only.
• Keep the public predicate `is_claim_covered/N` unchanged (same name & arity).
• Retain comments explaining rule blocks.
• Return **only** the full updated Prolog program, no extra prose.
"""

# † Variables injected: {contract_text}, {test}
TEST_MUTATION_PROMPT = """
You are mutating ONE Prolog test case for the insurance contract below in order
to explore a *different* scenario while keeping the same predicate names and
arity.

================  CONTEXT  ================
--- INSURANCE CONTRACT (excerpt) ---
{contract_text}

--- ORIGINAL TEST ---
{test}
===========================================

GUIDELINES
----------
1. Produce exactly **one** new test case formatted as:
     % Args: …
     test("label", is_claim_covered(...)).
2. Use `is_claim_covered` as the only top-level predicate queried.
3. Respect all earlier conventions (relative dates, `\+` for negation, no
   keyword arguments, etc.).
4. Return *only* Prolog code - comment line + test fact - nothing else.
5. Ideally keep the same arity as the original test, i.e., same number of arguments in is_claim_covered.
"""



# ----------- SYNTAX REPAIR PROMPT -----------
SYNTAX_REPAIR_PROMPT = """
You are fixing ONE Prolog program that **fails to compile** because of the
syntax error shown below.  Keep predicate names/arity unchanged unless the
error itself demands it.  Return **only** the corrected Prolog source – no
explanations, no markdown fencing.

----- ORIGINAL PROGRAM -----
{program}

----- SWI-Prolog SYNTAX ERROR -----
{error}
"""