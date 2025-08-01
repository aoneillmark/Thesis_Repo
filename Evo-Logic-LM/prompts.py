


# --- Candidate solution ---------------------------------------------------------------

Z3_NOTATION_SUMMARY = """
Here is a summary of the Z3 notation and its basic usage in Python:

# Z3Py Summary (Condensed)

Z3Py is the Python interface for the Z3 theorem prover. It enables modeling and solving logical/mathematical problems.

---

## 🔤 Syntax Summary

### 📌 Basics

```python
Int('x'), Real('y'), Bool('p')         # Variable creation
solve(expr1, expr2, ...)               # Solve constraints
simplify(expr)                         # Simplify expressions
```

### 🧠 Strategies

```python
simplify(expr, option=True)            # e.g., som=True, mul_to_power=True
set_option(html_mode=False)            # Control display
set_option(precision=30)               # Floating point precision
```

### 🔁 Fixpoints (Functions)

```python
f = Function('f', IntSort(), IntSort())    # Uninterpreted function
solve(f(f(x)) == x, f(x) == y, x != y)     # Reasoning about fixpoints
```

### ⚙️ Advanced Features

* **Bit-Vectors**

```python
BitVec('x', 32), BitVecVal(10, 32)     # Machine integers
ULT(x, 0), x >> 2, x & y               # Unsigned ops and bitwise
```

* **Expression Inspection**

```python
expr.num_args(), expr.children(), expr.decl().name()
```

* **Arithmetic**

```python
ToReal(IntExpr), Q(1,3), RealVal(1)
```

### 🐍 Z3Py API (Pythonic Interface)

```python
s = Solver()
s.add(...)
s.check()
s.model()
```

### 🧩 Z3 API (Low-level Features)

* Model inspection: `model()[var]`, `model().evaluate(expr)`
* Expression printing: `expr.sexpr()`

### 🐍 Z3 API in Python

* **Vectors and Lists**

```python
IntVector('x', 5), [ Int('x_%s' % i) for i in range(n) ]
```

* **Logical building blocks**

```python
And(), Or(), Not(), Implies(), If()
```

---
"""



# --- Prompt Definition ---
Z3_CANDIDATE_SOLUTION_PROMPT = Z3_NOTATION_SUMMARY + """
Given a problem description and a question. The task is to formulate the problem as a logic program, consisting two parts: Declarations and Constraints. The Options will be written by the user.
Declarations: Declare the variables and functions.
Constraints: Write the constraints in the problem description as logic formulas.
Options: The options in the question as logic formulas.
------
Problem:
On Tuesday Vladimir and Wendy each eat exactly four separate meals: breakfast, lunch, dinner, and a snack. The following is all that is known about what they eat during that day: At no meal does Vladimir eat the same kind of food as Wendy. Neither of them eats the same kind of food more than once during the day. For breakfast, each eats exactly one of the following: hot cakes, poached eggs, or omelet. For lunch, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet. For dinner, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet. For a snack, each eats exactly one of the following: fish or omelet. Wendy eats an omelet for lunch.
Question:
Vladimir must eat which one of the following foods?
Choices:
(A) fish
(B) hot cakes
(C) macaroni
(D) omelet
(E) poached eggs
###
# Declarations
people = EnumSort([Vladimir, Wendy])
meals = EnumSort([breakfast, lunch, dinner, snack])
foods = EnumSort([fish, hot_cakes, macaroni, omelet, poached_eggs])
eats = Function([people, meals] -> [foods])

# Constraints
ForAll([m:meals], eats(Vladimir, m) != eats(Wendy, m)) ::: At no meal does Vladimir eat the same kind of food as Wendy
ForAll([p:people, f:foods], Count([m:meals], eats(p, m) == f) <= 1) ::: Neither of them eats the same kind of food more than once during the day
ForAll([p:people], Or(eats(p, breakfast) == hot_cakes, eats(p, breakfast) == poached_eggs, eats(p, breakfast) == omelet)) ::: For breakfast, each eats exactly one of the following: hot cakes, poached eggs, or omelet
ForAll([p:people], Or(eats(p, lunch) == fish, eats(p, lunch) == hot_cakes, eats(p, lunch) == macaroni, eats(p, lunch) == omelet)) ::: For lunch, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
ForAll([p:people], Or(eats(p, dinner) == fish, eats(p, dinner) == hot_cakes, eats(p, dinner) == macaroni, eats(p, dinner) == omelet)) ::: For dinner, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
ForAll([p:people], Or(eats(p, snack) == fish, eats(p, snack) == omelet)) ::: For a snack, each eats exactly one of the following: fish or omelet
eats(Wendy, lunch) == omelet ::: Wendy eats an omelet for lunch

# Options
Question ::: Vladimir must eat which one of the following foods?
is_valid(Exists([m:meals], eats(Vladimir, m) == fish)) ::: (A)
is_valid(Exists([m:meals], eats(Vladimir, m) == hot_cakes)) ::: (B)
is_valid(Exists([m:meals], eats(Vladimir, m) == macaroni)) ::: (C)
is_valid(Exists([m:meals], eats(Vladimir, m) == omelet)) ::: (D)
is_valid(Exists([m:meals], eats(Vladimir, m) == poached_eggs)) ::: (E)
------
Problem:
In a repair facility there are exactly six technicians: Stacy, Urma, Wim, Xena, Yolanda, and Zane. Each technician repairs machines of at least one of the following three types—radios, televisions, and VCRs—and no other types. The following conditions apply: Xena and exactly three other technicians repair radios. Yolanda repairs both televisions and VCRs. Stacy does not repair any type of machine that Yolanda repairs. Zane repairs more types of machines than Yolanda repairs. Wim does not repair any type of machine that Stacy repairs. Urma repairs exactly two types of machines.
Question:
Which one of the following pairs of technicians could repair all and only the same types of machines as each other?
Choices:
(A) Stacy and Urma
(B) Urma and Yolanda
(C) Urma and Xena
(D) Wim and Xena
(E) Xena and Yolanda
###
# Declarations
technicians = EnumSort([Stacy, Urma, Wim, Xena, Yolanda, Zane])
machines = EnumSort([radios, televisions, VCRs])
repairs = Function([technicians, machines] -> [bool])

# Constraints
ForAll([t:technicians], Count([m:machines], repairs(t, m)) >= 1) ::: each technician repairs machines of at least one of the following three types
And(repairs(Xena, radios), Count([t:technicians], And(t != Xena, repairs(t, radios))) == 3) ::: Xena and exactly three other technicians repair radios
And(repairs(Yolanda, televisions), repairs(Yolanda, VCRs)) ::: Yolanda repairs both televisions and VCRs
ForAll([m:machines], Implies(repairs(Yolanda, m), Not(repairs(Stacy, m)))) ::: Stacy does not repair any type of machine that Yolanda repairs
Count([m:machines], repairs(Zane, m)) > Count([m:machines], repairs(Yolanda, m)) ::: Zane repairs more types of machines than Yolanda repairs
ForAll([m:machines], Implies(repairs(Stacy, m), Not(repairs(Wim, m)))) ::: Wim does not repair any type of machine that Stacy repairs
Count([m:machines], repairs(Urma, m)) == 2 ::: Urma repairs exactly two types of machines

# Options
Question ::: ::: Which one of the following pairs of technicians could repair all and only the same types of machines as each other?
is_sat(ForAll([m:machines], repairs(Stacy, m) == repairs(Urma, m))) ::: (A)
is_sat(ForAll([m:machines], repairs(Urma, m) == repairs(Yolanda, m))) ::: (B)
is_sat(ForAll([m:machines], repairs(Urma, m) == repairs(Xena, m))) ::: (C)
is_sat(ForAll([m:machines], repairs(Wim, m) == repairs(Xena, m))) ::: (D)
is_sat(ForAll([m:machines], repairs(Xena, m) == repairs(Yolanda, m))) ::: (E)
------
Problem:
Workers at a water treatment plant open eight valves—G, H, I, K, L, N, O, and P—to flush out a system of pipes that needs emergency repairs. To maximize safety and efficiency, each valve is opened exactly once, and no two valves are opened at the same time. The valves are opened in accordance with the following conditions: Both K and P are opened before H. O is opened before L but after H. L is opened after G. N is opened before H. I is opened after K.
Question: Each of the following could be the fifth valve opened EXCEPT:
Choices:
(A) H
(B) I
(C) K
(D) N
(E) O
###
# Declarations
valves = EnumSort([G, H, I, K, L, N, O, P])
opened = Function([valves] -> [int])
ForAll([v:valves], And(1 <= opened(v), opened(v) <= 8))

# Constraints
Distinct([v:valves], opened(v)) ::: no two valves are opened at the same time
And(opened(K) < opened(H), opened(P) < opened(H)) ::: Both K and P are opened before H
And(opened(O) > opened(H), opened(O) < opened(L)) ::: O is opened before L but after H
opened(L) > opened(G) ::: L is opened after G
opened(N) < opened(H) ::: N is opened before H
opened(I) > opened(K) ::: I is opened after K

# Options
Question ::: Each of the following could be the fifth valve opened EXCEPT:
is_exception(is_sat(opened(H) == 5)) ::: (A)
is_exception(is_sat(opened(I) == 5)) ::: (B)
is_exception(is_sat(opened(K) == 5)) ::: (C)
is_exception(is_sat(opened(N) == 5)) ::: (D)
is_exception(is_sat(opened(O) == 5)) ::: (E)

------
Problem:
Five candidates for mayor—Q, R, S, T, and U—will each speak exactly once at each of three town meetings—meetings 1, 2, and 3. At each meeting, each candidate will speak in one of five consecutive time slots. No two candidates will speak in the same time slot as each other at any meeting. The order in which the candidates will speak will meet the following conditions: Each candidate must speak either first or second at at least one of the meetings. Any candidate who speaks fifth at any of the meetings must speak first at at least one of the other meetings. No candidate can speak fourth at more than one of the meetings.
Question:
If R speaks second at meeting 2 and first at meeting 3, which one of the following is a complete and accurate list of those time slots any one of which could be the time slot in which R speaks at meeting 1?
Choices:
(A) fourth, fifth
(B) first, second, fifth
(C) second, third, fifth
(D) third, fourth, fifth
(E) second, third, fourth, fifth
###
# Declarations
candidates = EnumSort([Q, R, S, T, U])
meetings = EnumSort([1, 2, 3])
speaks = Function([meetings, candidates] -> [int])
ForAll([m:meetings, c:candidates], And(1 <= speaks(m, c), speaks(m, c) <= 5))

# Constraints
ForAll([m:meetings], Distinct([c:candidates], speaks(m, c))) ::: no two candidates will speak in the same time slot as each other at any meeting
ForAll([c:candidates], Exists([m:meetings], Or(speaks(m, c) == 1, speaks(m, c) == 2))) ::: each candidate must speak either first or second at at least one of the meetings
ForAll([c:candidates], Implies(Exists([m:meetings], speaks(m, c) == 5), Exists([m:meetings], speaks(m, c) == 1))) ::: any candidate who speaks fifth at any of the meetings must speak first at at least one of the other meetings
ForAll([c:candidates], Count([m:meetings], speaks(m, c) == 4) <= 1) ::: no candidate can speak fourth at more than one of the meetings
And(speaks(2, R) == 2, speaks(3, R) == 1) ::: if R speaks second at meeting 2 and first at meeting 3

# Options
Question ::: Which one of the following is a complete and accurate list of those time slots any one of which could be the time slot in which R speaks at meeting 1?
is_accurate_list([speaks(1, R) == 4, speaks(1, R) == 5]) ::: (A)
is_accurate_list([speaks(1, R) == 1, speaks(1, R) == 2, speaks(1, R) == 5]) ::: (B)
is_accurate_list([speaks(1, R) == 2, speaks(1, R) == 3, speaks(1, R) == 5]) ::: (C)
is_accurate_list([speaks(1, R) == 3, speaks(1, R) == 4, speaks(1, R) == 5]) ::: (D)
is_accurate_list([speaks(1, R) == 2, speaks(1, R) == 3, speaks(1, R) == 4, speaks(1, R) == 5]) ::: (E)

------
Problem:
A travel magazine has hired six interns—Farber, Gombarick, Hall, Jackson, Kanze, and Lha—to assist in covering three stories—Romania, Spain, and Tuscany. Each intern will be trained either as a photographer's assistant or as a writer's assistant. Each story is assigned a team of two interns—one photographer's assistant and one writer's assistant—in accordance with the following conditions: Gombarick and Lha will be trained in the same field. Farber and Kanze will be trained in different fields. Hall will be trained as a photographer's assistant. Jackson is assigned to Tuscany. Kanze is not assigned to Spain.
Question:
Which one of the following interns CANNOT be assigned to Tuscany?
Choices:
(A) Farber
(B) Gombarick
(C) Hall
(D) Kanze
(E) Lha
###
# Declarations
interns = EnumSort([Farber, Gombarick, Hall, Jackson, Kanze, Lha])
stories = EnumSort([Romania, Spain, Tuscany])
assistants = EnumSort([photographer, writer])
assigned = Function([interns] -> [stories])
trained = Function([interns] -> [assistants])

# Constraints
ForAll([s:stories], Exists([i1:interns, i2:interns], And(i1 != i2, And(assigned(i1) == s, assigned(i2) == s, trained(i1) == photographer, trained(i2) == writer)))) ::: each story is assigned a team of two interns—one photographer's assistant and one writer's assistant
trained(Gombarick) == trained(Lha) ::: Gombarick and Lha will be trained in the same field
trained(Farber) != trained(Kanze) ::: Farber and Kanze will be trained in different fields
trained(Hall) == photographer ::: Hall will be trained as a photographer's assistant
assigned(Jackson) == Tuscany ::: Jackson is assigned to Tuscany
assigned(Kanze) != Spain ::: Kanze is not assigned to Spain

# Options
Question ::: Which one of the following interns CANNOT be assigned to Tuscany?
is_unsat(assigned(Farber) == Tuscany) ::: (A)
is_unsat(assigned(Gombarick) == Tuscany) ::: (B)
is_unsat(assigned(Hall) == Tuscany) ::: (C)
is_unsat(assigned(Kanze) == Tuscany) ::: (D)
is_unsat(assigned(Lha) == Tuscany) ::: (E)

------
Now here is the problem description. Please write the Declarations and Constraints sections. DO NOT write the Options section.
Problem:
{PROBLEM}
"""
# --- Test Generation Prompt ------------------------------------------------------------
Z3_TEST_SUITE_GENERATION_PROMPT =  Z3_NOTATION_SUMMARY + """
You are designing multiple-choice test cases for the scenario below.

GOAL  
Produce exactly {num_cases} independent test-case blocks.  
Each block must follow the *exact* format shown in the sample below, with the
correct option marked by an asterisk.

RULES
1. Start each block with a natural-language **Question:** line.
2. Immediately follow with the header:  # Options
3. Repeat the same English question after “Question :::”.
4. Provide five option lines labelled (A)-(E), each containing **one** Z3
   expression followed by “::: (LABEL)”.  Put “*” right after the label of the
   single correct option, e.g.  ::: (C) *
5. Use only predicates, functions, constants, and sorts that already appear in
   the scenario (or are obvious enum constants).  Keep the logic expressions
   short—wrap them in helpers such as  is_sat( … ),  is_valid( … ), etc.
6. **Do not** output # Declarations or # Constraints in this prompt.
7. Separate consecutive test-case blocks with a line containing exactly five
   hash characters:

#####
SAMPLE BLOCK (FORMAT ONLY — DO NOT COPY CONTENT)
Given sample problem:
"Six delivery drones—D1, D2, D3, D4, D5, and D6—must each make exactly one delivery in each of three zones: Zone A, Zone B, and Zone C.
For every zone there are six delivery positions, numbered 1 (earliest) through 6 (latest), and no two drones deliver in the same position in the same zone.
The schedule must satisfy all of the following conditions:
- Each drone delivers either first or second in at least one zone.
- Any drone that delivers sixth in any zone must also deliver first in at least one other zone.
- In Zone A, D1 delivers earlier than D3.
- In Zone B, D4 delivers immediately before D5 (i.e., in consecutive positions with D4 earlier).
- D6 never delivers in position 4 in any zone.
"

GENERATED TEST CASES:

Question:
If D3 delivers second in Zone B and fifth in Zone C, which one of the following is a complete and accurate list of those delivery positions any one of which could be the delivery position in which D3 delivers in Zone A?
Choices:
(A) second, third
(B) first, second, third
(C) second, third, fourth
(D) third, fourth, fifth
(E) second, third, fourth, fifth
# Options
Question ::: Which one of the following is a complete and accurate list of those delivery positions any one of which could be the delivery position in which D3 delivers in Zone A?
is_accurate_list([deliver(A, D3) == 2, deliver(A, D3) == 3]) ::: (A)
is_accurate_list([deliver(A, D3) == 1, deliver(A, D3) == 2, deliver(A, D3) == 3]) ::: (B)
is_accurate_list([deliver(A, D3) == 2, deliver(A, D3) == 3, deliver(A, D3) == 4]) ::: (C)
is_accurate_list([deliver(A, D3) == 3, deliver(A, D3) == 4, deliver(A, D3) == 5]) ::: (D)
is_accurate_list([deliver(A, D3) == 2, deliver(A, D3) == 3, deliver(A, D3) == 4, deliver(A, D3) == 5]) ::: (E) *

#####

Question:
Which one of the following must be true?
Choices:
(A) In Zone A, D1 delivers earlier than D3.
(B) In Zone C, D6 delivers fourth.
(C) Some zone has D2 delivering sixth.
(D) In Zone B, D4 delivers later than D5.
(E) D1 delivers first in Zone B.
# Options
Question ::: Which one of the following must be true?
is_valid(deliver(A, D1) < deliver(A, D3)) ::: (A) *
is_valid(deliver(C, D6) == 4) ::: (B)
is_valid(Exists([z:zones], deliver(z, D2) == 6)) ::: (C)
is_valid(deliver(B, D4) > deliver(B, D5)) ::: (D)
is_valid(deliver(B, D1) == 1) ::: (E)

#####

Question:
Each of the following could be the delivery position in which D6 delivers in Zone A EXCEPT:
Choices:
(A) first
(B) second
(C) third
(D) fourth
(E) fifth
# Options
Question ::: Each of the following could be the delivery position in which D6 delivers in Zone A EXCEPT:
is_exception(is_sat(deliver(A, D6) == 1)) ::: (A)
is_exception(is_sat(deliver(A, D6) == 2)) ::: (B)
is_exception(is_sat(deliver(A, D6) == 3)) ::: (C)
is_exception(is_sat(deliver(A, D6) == 4)) ::: (D) *
is_exception(is_sat(deliver(A, D6) == 5)) ::: (E)


----
You can use the following Z3 functions:
is_valid(expr) - checks if the expression is valid
is_sat(expr) - checks if the expression is satisfiable
is_unsat(expr) - checks if the expression is unsatisfiable
is_exception(expr) - returns not expr (checks if the expression is not true)
is_accurate_list(exprs) - returns is_valid(Or(exprs)) and all([is_sat(c) for c in exprs])



— End of rules —
Now we give you the problem description for you to generate test cases for.
{PROBLEM}

Now generate {num_cases} blocks in the format above.
"""



# PROGRAM_SYNTAX_REPAIR_PROMPT = """
# You are given a Z3 program that failed to run correctly due to syntax errors. Below are several failing test cases along with the corresponding error messages that were observed when this program was evaluated on them.

# Your task is to repair the **candidate program** so that it compiles and executes successfully under these tests.

# Guidelines:
# • Preserve the intent and structure of the original logic.
# • Correct only the syntax issues — do not change semantics unless absolutely required.
# • Make sure the repaired program defines all necessary types, functions, and constraints using valid Z3 syntax.

# ------

# Errors from failing test cases:
# {errors}

# ------

# Original Program:
# {program}

# ------

# Now write a repaired version of the program below. Use clean, correct Z3 syntax. Do not include any natural language comments or explanation.
# """

PROGRAM_SYNTAX_REPAIR_PROMPT =  Z3_NOTATION_SUMMARY + """
Task: Given the initial program and the error message, debug the following logic program.
------
>>> Initial Program:
# Declarations
children = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])
lockers = EnumSort([1, 2, 3, 4, 5])
assigned = Function([children] -> [lockers])
gender = Function([children] -> [EnumSort([boy, girl])])
>>> Error Message:
SyntaxError: closing parenthesis ']' does not match opening parenthesis '('
>>> Corrected Program:
# Declarations
children = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])
lockers = EnumSort([1, 2, 3, 4, 5])
genders = EnumSort([boy, girl])
assigned = Function([children] -> [lockers])
gender = Function([children] -> [genders])
------
>>> Initial Program:
# Constraints
ForAll([l:lockers], Or(Exists([c:children], assigned(c) == l), Exists([c1:children, c2:children], And(c1 != c2, And(assigned(c1) == l, assigned(c2) == l, gender(c1) != gender(c2)))))) ::: Each locker must be assigned to either one or two children, and each child must be assigned to exactly one locker
Exists([c:children, l:lockers], And(assigned(Juan) == l, assigned(c) == l, c != Juan)) ::: Juan must share a locker
ForAll([l:lockers], assigned(Rachel) != l Or Not(Exists([c:children], And(c != Rachel, assigned(c) == l)))) ::: Rachel cannot share a locker
ForAll([l:lockers], Implies(assigned(Nita) == l, And(assigned(Trisha) != l - 1, assigned(Trisha) != l + 1))) ::: Nita's locker cannot be adjacent to Trisha's locker
assigned(Fred) == 3 ::: Fred must be assigned to locker 3
And(assigned(Trisha) == 3, assigned(Marc) == 1, ForAll([c:children], Implies(c != Marc, assigned(c) != 1))) ::: if Trisha is assigned to locker 3 and Marc alone is assigned to locker 1
>>> Error Message:
SyntaxError: invalid syntax
>>> Corrected Program:
# Constraints
ForAll([l:lockers], Or(Exists([c:children], assigned(c) == l), Exists([c1:children, c2:children], And(c1 != c2, And(assigned(c1) == l, assigned(c2) == l, gender(c1) != gender(c2)))))) ::: Each locker must be assigned to either one or two children, and each child must be assigned to exactly one locker
Exists([c:children, l:lockers], And(assigned(Juan) == l, assigned(c) == l, c != Juan)) ::: Juan must share a locker
ForAll([l:lockers], Or(assigned(Rachel) != l, Not(Exists([c:children], And(c != Rachel, assigned(c) == l))))) ::: Rachel cannot share a locker
ForAll([l:lockers], Implies(assigned(Nita) == l, And(assigned(Trisha) != l - 1, assigned(Trisha) != l + 1))) ::: Nita's locker cannot be adjacent to Trisha's locker
assigned(Fred) == 3 ::: Fred must be assigned to locker 3
And(assigned(Trisha) == 3, assigned(Marc) == 1, ForAll([c:children], Implies(c != Marc, assigned(c) != 1))) ::: if Trisha is assigned to locker 3 and Marc alone is assigned to locker 1
------
>>> Initial Program:
# Declarations
days = EnumSort([Monday, Tuesday, Wednesday, Thursday, Friday])
divisions = EnumSort([Operations, Production, Sales])
toured = Function([days] -> [divisions])

# Constraints
Count([d:days], toured(d) == Operations) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Production) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Sales) >= 1 ::: Each division is toured at least once
toured(Monday) != Operations ::: The Operations division is not toured on Monday
>>> Error Message:
TypeError: '<' not supported between instances of 'DatatypeRef' and 'DatatypeRef'
>>> Corrected Program:
# Declarations
days = IntSort([Monday, Tuesday, Wednesday, Thursday, Friday])
divisions = EnumSort([Operations, Production, Sales])
toured = Function([days] -> [divisions])

# Constraints
And(Monday == 1, Tuesday == 2, Wednesday == 3, Thursday == 4, Friday == 5)
Count([d:days], toured(d) == Operations) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Production) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Sales) >= 1 ::: Each division is toured at least once
toured(Monday) != Operations ::: The Operations division is not toured on Monday
------


ENSURE that the program maintains # Declarations and # Constraints sections!
You should not include # Questions or # Options sections.

>>> Initial Program:
{program}
>>> Compiled Program:
{compiled_code}
>>> Error Message(s):
{errors}
>>> Corrected Program:


"""




TEST_SYNTAX_REPAIR_PROMPT = Z3_NOTATION_SUMMARY +  """
You are given a test case for a logic program written in Z3. This test case caused multiple candidate programs to fail due to shared syntax errors, which are listed below.

Your task is to revise the **test case block** to fix the syntax issues while preserving the intent and logical constraints of the test.

Guidelines:
• Keep the overall structure of the test case (e.g. options block, quantifiers, expressions).
• Correct only the syntax errors — do not alter the meaning or constraints unless necessary to make the test valid.
• Ensure that the resulting test case compiles cleanly when evaluated with the given programs.

Task: Given the initial program and the error message, debug the following logic program.
------ EXAMPLES ------
>>> Initial Program:
# Declarations
children = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])
lockers = EnumSort([1, 2, 3, 4, 5])
assigned = Function([children] -> [lockers])
gender = Function([children] -> [EnumSort([boy, girl])])
>>> Error Message:
SyntaxError: closing parenthesis ']' does not match opening parenthesis '('
>>> Corrected Program:
# Declarations
children = EnumSort([Fred, Juan, Marc, Paul, Nita, Rachel, Trisha])
lockers = EnumSort([1, 2, 3, 4, 5])
genders = EnumSort([boy, girl])
assigned = Function([children] -> [lockers])
gender = Function([children] -> [genders])
------
>>> Initial Program:
# Constraints
ForAll([l:lockers], Or(Exists([c:children], assigned(c) == l), Exists([c1:children, c2:children], And(c1 != c2, And(assigned(c1) == l, assigned(c2) == l, gender(c1) != gender(c2)))))) ::: Each locker must be assigned to either one or two children, and each child must be assigned to exactly one locker
Exists([c:children, l:lockers], And(assigned(Juan) == l, assigned(c) == l, c != Juan)) ::: Juan must share a locker
ForAll([l:lockers], assigned(Rachel) != l Or Not(Exists([c:children], And(c != Rachel, assigned(c) == l)))) ::: Rachel cannot share a locker
ForAll([l:lockers], Implies(assigned(Nita) == l, And(assigned(Trisha) != l - 1, assigned(Trisha) != l + 1))) ::: Nita's locker cannot be adjacent to Trisha's locker
assigned(Fred) == 3 ::: Fred must be assigned to locker 3
And(assigned(Trisha) == 3, assigned(Marc) == 1, ForAll([c:children], Implies(c != Marc, assigned(c) != 1))) ::: if Trisha is assigned to locker 3 and Marc alone is assigned to locker 1
>>> Error Message:
SyntaxError: invalid syntax
>>> Corrected Program:
# Constraints
ForAll([l:lockers], Or(Exists([c:children], assigned(c) == l), Exists([c1:children, c2:children], And(c1 != c2, And(assigned(c1) == l, assigned(c2) == l, gender(c1) != gender(c2)))))) ::: Each locker must be assigned to either one or two children, and each child must be assigned to exactly one locker
Exists([c:children, l:lockers], And(assigned(Juan) == l, assigned(c) == l, c != Juan)) ::: Juan must share a locker
ForAll([l:lockers], Or(assigned(Rachel) != l, Not(Exists([c:children], And(c != Rachel, assigned(c) == l))))) ::: Rachel cannot share a locker
ForAll([l:lockers], Implies(assigned(Nita) == l, And(assigned(Trisha) != l - 1, assigned(Trisha) != l + 1))) ::: Nita's locker cannot be adjacent to Trisha's locker
assigned(Fred) == 3 ::: Fred must be assigned to locker 3
And(assigned(Trisha) == 3, assigned(Marc) == 1, ForAll([c:children], Implies(c != Marc, assigned(c) != 1))) ::: if Trisha is assigned to locker 3 and Marc alone is assigned to locker 1
------
>>> Initial Program:
# Declarations
days = EnumSort([Monday, Tuesday, Wednesday, Thursday, Friday])
divisions = EnumSort([Operations, Production, Sales])
toured = Function([days] -> [divisions])

# Constraints
Count([d:days], toured(d) == Operations) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Production) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Sales) >= 1 ::: Each division is toured at least once
toured(Monday) != Operations ::: The Operations division is not toured on Monday
>>> Error Message:
TypeError: '<' not supported between instances of 'DatatypeRef' and 'DatatypeRef'
>>> Corrected Program:
# Declarations
days = IntSort([Monday, Tuesday, Wednesday, Thursday, Friday])
divisions = EnumSort([Operations, Production, Sales])
toured = Function([days] -> [divisions])

# Constraints
And(Monday == 1, Tuesday == 2, Wednesday == 3, Thursday == 4, Friday == 5)
Count([d:days], toured(d) == Operations) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Production) >= 1 ::: Each division is toured at least once
Count([d:days], toured(d) == Sales) >= 1 ::: Each division is toured at least once
toured(Monday) != Operations ::: The Operations division is not toured on Monday
------------------

------

Failing Programs and Syntax Errors:
{prog_snips}

>>> Compiled Program:
{compiled_code}

------

Original Test Case:
{failing_query}

------
ENSURE that the test case maintains # Question and # Options sections!
You should not include # Declarations or # Constraints sections.
If the error is with the program and NOT the original test case, simply return the original test case unchanged.

Now write a repaired version of the test case block below.
"""
# If and only if you think the test case is already correct (and the issue lies with the program), simply return it unchanged.



# TEST_GENERATION_PROMPT = """
# You are given the text of an insurance contract.
# Your task is to generate a single Prolog test case that queries a hypothetical Prolog encoding of this contract to determine whether or not a specific scenario is covered by the policy.

# Insurance contract:
# {contract_text}

# Instructions:
# 1. Return exactly 1 Prolog test case in the form:
#    test("label", prolog_query).
# **Immediately above the test case, add a single-line Prolog comment (starting
#    with `%`) that concisely explains what each argument of the query means.**
#    Example:
#      % Args: Name, DateOfBirth, Gender
#      test("basic_cover", is_mcdonalds_customer('Johnny Appleseed', 01011973, Male)).
# 2. The test case must be a valid Prolog fact, and must include a string label as the first argument and a valid Prolog *query* as the second — NOT a rule or clause. Do NOT include the `:-` operator in the test.
# 3. The test case should target a specific aspect of the policy — e.g., coverage conditions, exclusions, age requirements, timing, etc.
# 4. DO NOT include any explanation or text. Only output Prolog code.
# 5. The test case must use predicates that would exist in a reasonable encoding of the insurance contract.
# 6. The test case must only query the public-facing predicate `is_claim_covered` to determine whether a claim is covered. Do not directly test helper or internal predicates like `is_policy_in_effect`, `policy_canceled`, or `condition_wellness_visit_satisfied`.
# 7. The test case must represent a complete claim scenario and assert whether coverage applies.
# 8. If using compound goals (e.g., intermediate variable bindings), wrap them in parentheses, and separate them with commas.
# 9. DO NOT use `not`. Use `\+` for negation in Prolog.
# 10. Assume that all dates/times in any query to this code (apart from the claimant's age) will be given RELATIVE to the effective date of the policy (i.e., there will never be a need to calculate the time elapsed between two dates). Take dates RELATIVE TO the effective date into account when writing this encoding.
# 11. Assume that the agreement has been signed and the premium has been paid (on time). There is no need to encode rules or facts for these conditions.
# 12. All dates should be integer values representing days relative to the policy's effective date, e.g., `0` for the effective date, `1` for one day later, etc. Do not use absolute dates or words.
# 13. DO NOT define new predicates, rules, or clauses inside the test case. Only use an executable query that can be run in isolation.
# 14. Ensure your test uses consistent predicate names and arities with is_claim_covered/x.
# 15. Do NOT use keyword-style arguments like key=value. Prolog does not support this syntax. DO NOT use this style in your query.

# We have a number of test cases that have already been run against the Prolog code, some of which have passed and some of which have failed.
# Your task is to generate a new test case that is consistent with the existing tests (function signature and arity), but which explores a different scenario.
# Identify potential problems or edge cases in the program. Focus on gaps in logic or unusual scenarios. It's best if you can think of a unique scenario that has not been tested before, which is consistent with the rules of the contract text.

# Here's the best program so far:
# {program}

# Here are the tests that the best program has failed:
# {failing}

# Here are the tests that the best program has passed:
# {passing}
# """

Z3_TEST_GENERATION_PROMPT = """
You are designing a **single** multiple-choice test question for the logic scenario below.

SCENARIO
--------
{contract_text}

GOAL  
Write exactly **one** test-case block in the format shown below. It should test the solver’s understanding of the scenario using logic-based options.

RULES
1. Begin with a natural-language **Question:** line.
2. Follow with:  # Options
3. Repeat the question after “Question :::”.
4. Provide five answer options labelled (A)–(E). Each option must:
   - contain one logic expression (e.g., `is_sat(...)`, `is_valid(...)`, etc.),
   - end with “::: (LABEL)”, e.g.,  `::: (C)`.
   - mark **only one correct option** with an asterisk, like  `::: (C) *`.
5. All functions, variables, and constants used in the logic expressions must come from the scenario above—do not invent new ones.
6. Keep the logic concise and readable.

SAMPLE FORMAT (for illustration only):

Question:
Which one of the following must be true?
Choices:
(A) In Zone A, D1 delivers earlier than D3.
(B) In Zone C, D6 delivers fourth.
(C) Some zone has D2 delivering sixth.
(D) In Zone B, D4 delivers later than D5.
(E) D1 delivers first in Zone B.
# Options
Question ::: Which one of the following must be true?
is_valid(deliver(A, D1) < deliver(A, D3)) ::: (A) *
is_valid(deliver(C, D6) == 4) ::: (B)
is_valid(Exists([z:zones], deliver(z, D2) == 6)) ::: (C)
is_valid(deliver(B, D4) > deliver(B, D5)) ::: (D)
is_valid(deliver(B, D1) == 1) ::: (E)

— End of rules —

Now generate one test case in this format for the scenario provided above.
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


