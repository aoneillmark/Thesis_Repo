# utils.py
import math
from dotenv import load_dotenv
import google.generativeai as genai
import os
import random
import re
from google.api_core import exceptions as gexp   
import time

# import datetime
# timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# log_dir = f"logs/run_{timestamp}"
# os.makedirs(log_dir, exist_ok=True)

def calculate_test_conf(test_idx, code_population, matrix):
    passed = 0.0
    total = 0.0
    for c in code_population:
        code_idx = int(c['idx'])
        fitness = c['fitness']
        if matrix[code_idx][test_idx]:
            passed += fitness
        total += fitness
    return 0.0 if total == 0.0 else passed / total

def calculate_test_disc(test_idx, code_population, matrix):
    passed = 0.0
    total = 0.0
    for c in code_population:
        code_idx = int(c['idx'])
        if matrix[code_idx][test_idx]:
            passed += 1
        total += 1
    p = 0.0 if total == 0.0 else passed / total
    if p == 0.0 or p == 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))

# def save_solutions(solutions, iteration=None):
#     iter_dir = os.path.join(log_dir, f"iter_{iteration:02d}") if iteration else log_dir
#     os.makedirs(iter_dir, exist_ok=True)
#     for sol in solutions:
#         sol.canonical_program = sol.original_program
#         fname = os.path.join(iter_dir, f"solution_{sol.id}.pl")
#         with open(fname, "w", encoding="utf-8") as f:
#             f.write(sol.canonical_program or "❌ No canonical program available.")

# def save_test_cases(test_cases, iteration=None):
#     iter_dir = os.path.join(log_dir, f"iter_{iteration:02d}") if iteration else log_dir
#     os.makedirs(iter_dir, exist_ok=True)
#     for tc in test_cases:
#         tc.canonical_fact = tc.original_fact
#     test_log = os.path.join(iter_dir, "test_cases.pl")
#     with open(test_log, "w", encoding="utf-8") as f:
#         for tc in test_cases:
#             f.write((tc.canonical_fact or "❌ Invalid test case") + "\n")

# --- Configuration ---
load_dotenv()
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("❌ Error: GEMINI_API_KEY environment variable not set.")
    exit()

# model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-06-17') # RPM: 15, TPM: 250,000, RPD: 1,000
# model = genai.GenerativeModel('gemini-2.5-flash-lite')
# model = genai.GenerativeModel('gemini-2.5-flash')

generation_config = genai.types.GenerationConfig(
    max_output_tokens=8192,        # Maximum tokens in response
)

model = genai.GenerativeModel(
    'models/gemini-2.5-flash-lite-preview-06-17',
    generation_config=generation_config
)

# ---------------------------------------------------------------------------
# internal
# ---------------------------------------------------------------------------
_retry_secs_re = re.compile(r"retry_delay\s*{\s*seconds:\s*(\d+)")

def _next_delay(prev, cap=60):
    """Exponential back-off with jitter, capped at `cap` seconds."""
    base = min(prev * 2, cap)
    return base + random.uniform(0, base * 0.15)      # ±15 % jitter

# ---------------------------------------------------------------------------
# public
# ---------------------------------------------------------------------------
def generate_content(prompt, *, is_json=False,
                     max_retries=6, init_delay=4):
    """
    Call Gemini with automatic retries on transient errors
    (429, 503, network glitches). Returns `None` only after
    exhausting all retries.
    """
    delay = init_delay
    for attempt in range(1, max_retries + 1):
        try:
            resp = model.generate_content(
                prompt
            )
            # if not resp or not resp.text:
            #     print("❌  Empty LLM response")
            #     return None

            if (not resp) or (not resp.text.strip()):
                raise gexp.DeadlineExceeded("empty-text")  # reuse an existing retryable type
            
            text = resp.text.strip()
            if "```" in text:
                lang = "json" if is_json else "prolog"
                text = text.split(f"```{lang}\n", 1)[-1].split("\n```", 1)[0]
            return text

        # ---------- transient / quota errors ----------
        except (gexp.TooManyRequests, gexp.ServiceUnavailable,
                gexp.DeadlineExceeded) as e:
            # honour server-suggested retry_delay if present
            srv_wait = getattr(e, "retry_delay", None)
            if not srv_wait:
                # sometimes the delay is only in the text blob ➜ parse it
                m = _retry_secs_re.search(str(e))
                srv_wait = int(m.group(1)) if m else None
            wait = srv_wait.seconds if hasattr(srv_wait, "seconds") else srv_wait
            if not wait:
                wait = delay
                delay = _next_delay(delay)

            print(f"⚠️  {type(e).__name__} (attempt {attempt}/{max_retries}) "
                  f"– sleeping {wait:.1f}s")
            time.sleep(wait)
            continue

        # ---------- other errors ----------
        except Exception as e:
            print(f"❗️ LLM Generation Error (fatal): {e}")
            return None

    print("❌  Exhausted retries without success.")
    return None