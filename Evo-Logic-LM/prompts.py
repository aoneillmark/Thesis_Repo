# LOGIC_LM_PROMPT = """
# Given a problem description and a question. The task is to parse the problem and the question into first-order logic formulars.
# The grammar of the first-order logic formular is defined as follows:
# 1) logical conjunction of expr1 and expr2: expr1 ∧ expr2
# 2) logical disjunction of expr1 and expr2: expr1 ∨ expr2
# 3) logical exclusive disjunction of expr1 and expr2: expr1 ⊕ expr2
# 4) logical negation of expr1: ¬expr1
# 5) expr1 implies expr2: expr1 → expr2
# 6) expr1 if and only if expr2: expr1 ↔ expr2
# 7) logical universal quantification: ∀x
# 8) logical existential quantification: ∃x
# ------
# # Problem:
# All people who regularly drink coffee are dependent on caffeine. People either regularly drink coffee or joke about being addicted to caffeine. No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# # Question:
# Based on the above information, is the following statement true, false, or uncertain? Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug.
# Based on the above information, is the following statement true, false, or uncertain? If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee.
# ###
# # Predicates:
# Dependent(x) ::: x is a person dependent on caffeine.
# Drinks(x) ::: x regularly drinks coffee.
# Jokes(x) ::: x jokes about being addicted to caffeine.
# Unaware(x) ::: x is unaware that caffeine is a drug.
# Student(x) ::: x is a student.
# # Premises:
# ∀x (Drinks(x) → Dependent(x)) ::: All people who regularly drink coffee are dependent on caffeine.
# ∀x (Drinks(x) ⊕ Jokes(x)) ::: People either regularly drink coffee or joke about being addicted to caffeine.
# ∀x (Jokes(x) → ¬Unaware(x)) ::: No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. 
# (Student(rina) ∧ Unaware(rina)) ⊕ ¬(Student(rina) ∨ Unaware(rina)) ::: Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. 
# ¬(Dependent(rina) ∧ Student(rina)) → (Dependent(rina) ∧ Student(rina)) ⊕ ¬(Dependent(rina) ∨ Student(rina)) ::: If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# # Conclusion:
# Jokes(rina) ⊕ Unaware(rina) ::: Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug.
# ((Jokes(rina) ∧ Unaware(rina)) ⊕ ¬(Jokes(rina) ∨ Unaware(rina))) → (Jokes(rina) ∧ Drinks(rina)) ::: If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee.
# ------
# # Problem:
# Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music. Any choral conductor is a musician. Some musicians love music. Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# # Question:
# Based on the above information, is the following statement true, false, or uncertain? Miroslav Venhoda loved music.
# Based on the above information, is the following statement true, false, or uncertain? A Czech person wrote a book in 1946.
# Based on the above information, is the following statement true, false, or uncertain? No choral conductor specialized in the performance of Renaissance.
# ###
# # Predicates:
# Czech(x) ::: x is a Czech person.
# ChoralConductor(x) ::: x is a choral conductor.
# Musician(x) ::: x is a musician.
# Love(x, y) ::: x loves y.
# Author(x, y) ::: x is the author of y.
# Book(x) ::: x is a book.
# Publish(x, y) ::: x is published in year y.
# Specialize(x, y) ::: x specializes in y.
# # Premises:
# Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
# ∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
# ∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
# Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# # Conclusion:
# Love(miroslav, music) ::: Miroslav Venhoda loved music.
# ∃y ∃x (Czech(x) ∧ Author(x, y) ∧ Book(y) ∧ Publish(y, year1946)) ::: A Czech person wrote a book in 1946.
# ¬∃x (ChoralConductor(x) ∧ Specialize(x, renaissance)) ::: No choral conductor specialized in the performance of Renaissance.
# ------
# # Problem:
# {PROBLEM}
# # Question:
# {QUESTION}
# ###
# """


FOLIO_NOTATION_SUMMARY = """
The grammar of the first-order logic formular is defined as follows:
1) logical conjunction of expr1 and expr2: expr1 ∧ expr2
2) logical disjunction of expr1 and expr2: expr1 ∨ expr2
3) logical exclusive disjunction of expr1 and expr2: expr1 ⊕ expr2
4) logical negation of expr1: ¬expr1
5) expr1 implies expr2: expr1 → expr2
6) expr1 if and only if expr2: expr1 ↔ expr2
7) logical universal quantification: ∀x
8) logical existential quantification: ∃x
"""


FOLIO_CANDIDATE_SOLUTION_PROMPT = FOLIO_NOTATION_SUMMARY + """
Given a problem description and a question. The task is to parse the problem and the question into first-order logic formulars.

Your job SPECIFICALLY is to generate the first-order logic predicates and premises that are necessary to answer the question.
You will be given a problem description and questions, as well as their conclusions. Therefore you do not need to write the # Problem, # Question or # Conclusion sections.
You should only write the # Predicates and # Premises sections.

I will provide you with some examples:
------
# Problem:
All people who regularly drink coffee are dependent on caffeine. People either regularly drink coffee or joke about being addicted to caffeine. No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# Question:
Based on the above information, is the following statement true, false, or uncertain? Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug.
Based on the above information, is the following statement true, false, or uncertain? If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee.
###
# Predicates:
Dependent(x) ::: x is a person dependent on caffeine.
Drinks(x) ::: x regularly drinks coffee.
Jokes(x) ::: x jokes about being addicted to caffeine.
Unaware(x) ::: x is unaware that caffeine is a drug.
Student(x) ::: x is a student.
# Premises:
∀x (Drinks(x) → Dependent(x)) ::: All people who regularly drink coffee are dependent on caffeine.
∀x (Drinks(x) ⊕ Jokes(x)) ::: People either regularly drink coffee or joke about being addicted to caffeine.
∀x (Jokes(x) → ¬Unaware(x)) ::: No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. 
(Student(rina) ∧ Unaware(rina)) ⊕ ¬(Student(rina) ∨ Unaware(rina)) ::: Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. 
¬(Dependent(rina) ∧ Student(rina)) → (Dependent(rina) ∧ Student(rina)) ⊕ ¬(Dependent(rina) ∨ Student(rina)) ::: If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# Conclusion:
Jokes(rina) ⊕ Unaware(rina) ::: Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug. TRUE
((Jokes(rina) ∧ Unaware(rina)) ⊕ ¬(Jokes(rina) ∨ Unaware(rina))) → (Jokes(rina) ∧ Drinks(rina)) ::: If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee. FALSE
------
# Problem:
Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music. Any choral conductor is a musician. Some musicians love music. Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# Question:
Based on the above information, is the following statement true, false, or uncertain? Miroslav Venhoda loved music.
Based on the above information, is the following statement true, false, or uncertain? A Czech person wrote a book in 1946.
Based on the above information, is the following statement true, false, or uncertain? No choral conductor specialized in the performance of Renaissance.
###
# Predicates:
Czech(x) ::: x is a Czech person.
ChoralConductor(x) ::: x is a choral conductor.
Musician(x) ::: x is a musician.
Love(x, y) ::: x loves y.
Author(x, y) ::: x is the author of y.
Book(x) ::: x is a book.
Publish(x, y) ::: x is published in year y.
Specialize(x, y) ::: x specializes in y.
# Premises:
Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# Conclusion:
Love(miroslav, music) ::: Miroslav Venhoda loved music. UNKNOWN
∃y ∃x (Czech(x) ∧ Author(x, y) ∧ Book(y) ∧ Publish(y, year1946)) ::: A Czech person wrote a book in 1946. FALSE
¬∃x (ChoralConductor(x) ∧ Specialize(x, renaissance)) ::: No choral conductor specialized in the performance of Renaissance. UNKNOWN
------

# Problem:
{PROBLEM}
# Question:
{QUESTION}
# Conclusion:
{CONCLUSION}

Do not write the # Problem, # Question, or # Conclusion sections.
Write the # Predicates: and # Premises: sections here:
"""


FOLIO_TEST_SUITE_PROMPT = FOLIO_NOTATION_SUMMARY + """
Given a problem description and a question. The task is to parse the problem, create new questions based on that problem, and translate them into first-order logic.

Your job SPECIFICALLY is to create new questions based on the problem, and generate the Conclusion sections in first-order logic that can be answered with the predicates and premises that will be generated separately.
You do not need to write the # Problem, # Predicates, or # Premises sections.
You should only write the # Question and # Conclusion sections.

I will provide you with some examples:
------
# Problem:
All people who regularly drink coffee are dependent on caffeine. People either regularly drink coffee or joke about being addicted to caffeine. No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# Question:
Based on the above information, is the following statement true, false, or uncertain? Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug.
Based on the above information, is the following statement true, false, or uncertain? If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee.
###
# Predicates:
Dependent(x) ::: x is a person dependent on caffeine.
Drinks(x) ::: x regularly drinks coffee.
Jokes(x) ::: x jokes about being addicted to caffeine.
Unaware(x) ::: x is unaware that caffeine is a drug.
Student(x) ::: x is a student.
# Premises:
∀x (Drinks(x) → Dependent(x)) ::: All people who regularly drink coffee are dependent on caffeine.
∀x (Drinks(x) ⊕ Jokes(x)) ::: People either regularly drink coffee or joke about being addicted to caffeine.
∀x (Jokes(x) → ¬Unaware(x)) ::: No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. 
(Student(rina) ∧ Unaware(rina)) ⊕ ¬(Student(rina) ∨ Unaware(rina)) ::: Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. 
¬(Dependent(rina) ∧ Student(rina)) → (Dependent(rina) ∧ Student(rina)) ⊕ ¬(Dependent(rina) ∨ Student(rina)) ::: If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# Conclusion:
Jokes(rina) ⊕ Unaware(rina) ::: Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug. TRUE
((Jokes(rina) ∧ Unaware(rina)) ⊕ ¬(Jokes(rina) ∨ Unaware(rina))) → (Jokes(rina) ∧ Drinks(rina)) ::: If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee. FALSE
------
# Problem:
Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music. Any choral conductor is a musician. Some musicians love music. Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# Question:
Based on the above information, is the following statement true, false, or uncertain? Miroslav Venhoda loved music.
Based on the above information, is the following statement true, false, or uncertain? A Czech person wrote a book in 1946.
Based on the above information, is the following statement true, false, or uncertain? No choral conductor specialized in the performance of Renaissance.
###
# Predicates:
Czech(x) ::: x is a Czech person.
ChoralConductor(x) ::: x is a choral conductor.
Musician(x) ::: x is a musician.
Love(x, y) ::: x loves y.
Author(x, y) ::: x is the author of y.
Book(x) ::: x is a book.
Publish(x, y) ::: x is published in year y.
Specialize(x, y) ::: x specializes in y.
# Premises:
Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# Conclusion:
Love(miroslav, music) ::: Miroslav Venhoda loved music. UNKNOWN
∃y ∃x (Czech(x) ∧ Author(x, y) ∧ Book(y) ∧ Publish(y, year1946)) ::: A Czech person wrote a book in 1946. FALSE
¬∃x (ChoralConductor(x) ∧ Specialize(x, renaissance)) ::: No choral conductor specialized in the performance of Renaissance. UNKNOWN
------

At the end of the conclusion, in the comment (i.e. after the ':::') write at the end of the comment whether the conclusion is TRUE, FALSE, or UNKNOWN.
^^^ This is very important!

Write {num_cases} new # Question and # Conclusion sections based on the problem below.
Include five hashtags (#####) between each section. 

i.e. if you are asked to write 2 sections, then write:
#####

# Question:
<Question 1>
# Conclusion:
<Conclusion 1>

#####

# Question:
<Question 2>
# Conclusion:
<Conclusion 2>


Here is the problem you need to work with:

# Problem:
{PROBLEM}


Write the # Question: and # Conclusion: sections here:
"""


PROGRAM_SYNTAX_REPAIR_PROMPT = FOLIO_NOTATION_SUMMARY + """
Task: Given the wrong FOL formula and the error message, output the correct FOL formula.
Your job is SPECIFICALLY to fix only the # Predicates and # Premises sections.
Therefore you do not need to write the # Problem, # Question or # Conclusion sections, even if there are errors in them.

Here are some examples:
------
>>> Initial Program:
# Premises:
MusicPiece(symphonyNo9) ::: Symphony No. 9 is a music piece.
∀x (Composer(x) → ∃y (Write(x, y) ∧ MusicPiece(y))) ::: Composers write music pieces.
Write(beethoven, symphonyNo9) ::: Beethoven wrote Symphony No. 9.
Lead(beethoven, viennaMusicSociety) ∧ Orchestra(viennaMusicSociety) ::: Vienna Music Society is an orchestra and Beethoven leads the Vienna Music Society.
∀x (Orchestra(x) → ∃y (Lead(y, x) ∧ Conductor(y))) ::: Orchestras are led by conductors.
# Conclusion:
¬Conductor(beethoven) ::: Beethoven is not a conductor. FALSE
>>> Error Message:
Parsing Error
>>> Correct Program:
# Premises:
MusicPiece(symphonyNo9) ::: Symphony No. 9 is a music piece.
∀x ∃z (¬Composer(x) ∨ (Write(x,z) ∧ MusicPiece(z))) ::: Composers write music pieces.
Write(beethoven, symphonyNo9) ::: Beethoven wrote Symphony No. 9.
Lead(beethoven, viennaMusicSociety) ∧ Orchestra(viennaMusicSociety) ::: Vienna Music Society is an orchestra and Beethoven leads the Vienna Music Society.
∀x ∃z (¬Orchestra(x) ∨ (Lead(z,x) ∧ Conductor(z))) ::: Orchestras are led by conductors.
# Conclusion:
¬Conductor(beethoven) ::: Beethoven is not a conductor. FALSE
------
>>> Initial Program:
# Predicates:
JapaneseCompany(x) ::: x is a Japanese game company.
Create(x, y) ::: x created the game y.
Top10(x) ::: x is in the Top 10 list.
Sell(x, y) ::: x sold more than y copies.
# Premises:
∃x (JapaneseCompany(x) ∧ Create(x, legendOfZelda)) ::: A Japanese game company created the game the Legend of Zelda.
∀x (Top10(x) → ∃y (JapaneseCompany(y) ∧ Create(y, x))) ::: All games in the Top 10 list are made by Japanese game companies.
∀x (Sell(x, oneMillion) → Top10(x)) ::: If a game sells more than one million copies, then it will be selected into the Top 10 list.
Sell(legendOfZelda, oneMillion) ::: The Legend of Zelda sold more than one million copies.
# Conclusion:
Top10(legendOfZelda) ::: The Legend of Zelda is in the Top 10 list. TRUE
>>> Error Message:
Parsing Error
>>> Correct Program:
# Predicates:
JapaneseCompany(x) ::: x is a Japanese game company.
Create(x, y) ::: x created the game y.
Top10(x) ::: x is in the Top 10 list.
Sell(x, y) ::: x sold more than y copies.
# Premises:
∃x (JapaneseCompany(x) ∧ Create(x, legendOfZelda)) ::: A Japanese game company created the game the Legend of Zelda.
∀x ∃z (¬Top10(x) ∨ (JapaneseCompany(z) ∧ Create(z,x))) ::: All games in the Top 10 list are made by Japanese game companies.
∀x (Sell(x, oneMillion) → Top10(x)) ::: If a game sells more than one million copies, then it will be selected into the Top 10 list.
Sell(legendOfZelda, oneMillion) ::: The Legend of Zelda sold more than one million copies.
# Conclusion:
Top10(legendOfZelda) ::: The Legend of Zelda is in the Top 10 list. TRUE
------
>>> Initial Program:
# Predicates:
Listed(x) ::: x is listed in Yelp’s recommendations.
NegativeReviews(x) ::: x receives many negative reviews.
Rating(x, y) ::: x has a rating of y.
TakeOut(x) ::: x provides take-out service.
Popular(x) ::: x is popular among local residents.
# Premises:
∀x (Listed(x) → ¬NegativeReviews(x)) ::: If the restaurant is listed in Yelp’s recommendations, then the restaurant does not receive many negative reviews.
∀x (Rating(x, y) ∧ y > 9 → Listed(x)) ::: All restaurants with a rating greater than 9 are listed in Yelp’s recommendations.
∃x (¬TakeOut(x) ∧ NegativeReviews(x)) ::: Some restaurants that do not provide take-out service receive many negative reviews.
∀x (Popular(x) → (Rating(x, y) ∧ y > 9)) ::: All restaurants that are popular among local residents have ratings greater than 9.
Rating(subway, y) ∧ y > 9 ∨ Popular(subway) ::: Subway has a rating greater than 9 or is popular among local residents.
# Conclusion:
TakeOut(subway) ∧ ¬NegativeReviews(subway) ::: Subway provides take-out service and does not receive many negative reviews. FALSE
>>> Error Message:
Parsing Error
>>> Correct Program:
# Predicates:
Listed(x) ::: x is listed in Yelp’s recommendations.
NegativeReviews(x) ::: x receives many negative reviews.
TakeOut(x) ::: x provides take-out service.
Popular(x) ::: x is popular among local residents.
GreaterThanNine(x) ::: x has a rating greater than 9.
# Premises:
∀x (Listed(x) → ¬NegativeReviews(x)) ::: If the restaurant is listed in Yelp’s recommendations, then the restaurant does not receive many negative reviews.
∀x (GreaterThanNine(x) → Listed(x)) ::: All restaurants with a rating greater than 9 are listed in Yelp’s recommendations.
∃x (¬TakeOut(x) ∧ NegativeReviews(x)) ::: Some restaurants that do not provide take-out service receive many negative reviews.
∀x (Popular(x) → GreaterThanNine(x)) ::: All restaurants that are popular among local residents have ratings greater than 9.
GreaterThanNine(subway) ∨ Popular(subway) ::: Subway has a rating greater than 9 or is popular among local residents.
# Conclusion:
TakeOut(subway) ∧ ¬NegativeReviews(subway) ::: Subway provides take-out service and does not receive many negative reviews. FALSE
------


DO NOT write the # Problem, # Question, or # Conclusion sections!!!
Here is the program you need to work with:

>>> Initial Program:
{PROGRAM}
>>> Error Message:
{ERROR_MESSAGE}
>>> Corrected Program:

"""


FOLIO_TEST_CASE_REPAIR_PROMPT = FOLIO_NOTATION_SUMMARY + """
Task: Given the wrong FOL formula and the error message, output the correct FOL formula.
Your job is SPECIFICALLY to fix only the # Question and # Conclusion sections.
Therefore you do not need to write the # Problem, # Predicates or # Premises sections

Here are some examples:
------
>>> Initial Program:
# Premises:
MusicPiece(symphonyNo9) ::: Symphony No. 9 is a music piece.
∀x (Composer(x) → ∃y (Write(x, y) ∧ MusicPiece(y))) ::: Composers write music pieces.
Write(beethoven, symphonyNo9) ::: Beethoven wrote Symphony No. 9.
Lead(beethoven, viennaMusicSociety) ∧ Orchestra(viennaMusicSociety) ::: Vienna Music Society is an orchestra and Beethoven leads the Vienna Music Society.
∀x (Orchestra(x) → ∃y (Lead(y, x) ∧ Conductor(y))) ::: Orchestras are led by conductors.
# Conclusion:
¬Conductor(beethoven) ::: Beethoven is not a conductor. FALSE
>>> Error Message:
Parsing Error
>>> Correct Program:
# Premises:
MusicPiece(symphonyNo9) ::: Symphony No. 9 is a music piece.
∀x ∃z (¬Composer(x) ∨ (Write(x,z) ∧ MusicPiece(z))) ::: Composers write music pieces.
Write(beethoven, symphonyNo9) ::: Beethoven wrote Symphony No. 9.
Lead(beethoven, viennaMusicSociety) ∧ Orchestra(viennaMusicSociety) ::: Vienna Music Society is an orchestra and Beethoven leads the Vienna Music Society.
∀x ∃z (¬Orchestra(x) ∨ (Lead(z,x) ∧ Conductor(z))) ::: Orchestras are led by conductors.
# Conclusion:
¬Conductor(beethoven) ::: Beethoven is not a conductor. FALSE
------
>>> Initial Program:
# Predicates:
JapaneseCompany(x) ::: x is a Japanese game company.
Create(x, y) ::: x created the game y.
Top10(x) ::: x is in the Top 10 list.
Sell(x, y) ::: x sold more than y copies.
# Premises:
∃x (JapaneseCompany(x) ∧ Create(x, legendOfZelda)) ::: A Japanese game company created the game the Legend of Zelda.
∀x (Top10(x) → ∃y (JapaneseCompany(y) ∧ Create(y, x))) ::: All games in the Top 10 list are made by Japanese game companies.
∀x (Sell(x, oneMillion) → Top10(x)) ::: If a game sells more than one million copies, then it will be selected into the Top 10 list.
Sell(legendOfZelda, oneMillion) ::: The Legend of Zelda sold more than one million copies.
# Conclusion:
Top10(legendOfZelda) ::: The Legend of Zelda is in the Top 10 list. TRUE
>>> Error Message:
Parsing Error
>>> Correct Program:
# Predicates:
JapaneseCompany(x) ::: x is a Japanese game company.
Create(x, y) ::: x created the game y.
Top10(x) ::: x is in the Top 10 list.
Sell(x, y) ::: x sold more than y copies.
# Premises:
∃x (JapaneseCompany(x) ∧ Create(x, legendOfZelda)) ::: A Japanese game company created the game the Legend of Zelda.
∀x ∃z (¬Top10(x) ∨ (JapaneseCompany(z) ∧ Create(z,x))) ::: All games in the Top 10 list are made by Japanese game companies.
∀x (Sell(x, oneMillion) → Top10(x)) ::: If a game sells more than one million copies, then it will be selected into the Top 10 list.
Sell(legendOfZelda, oneMillion) ::: The Legend of Zelda sold more than one million copies.
# Conclusion:
Top10(legendOfZelda) ::: The Legend of Zelda is in the Top 10 list. TRUE
------
>>> Initial Program:
# Predicates:
Listed(x) ::: x is listed in Yelp’s recommendations.
NegativeReviews(x) ::: x receives many negative reviews.
Rating(x, y) ::: x has a rating of y.
TakeOut(x) ::: x provides take-out service.
Popular(x) ::: x is popular among local residents.
# Premises:
∀x (Listed(x) → ¬NegativeReviews(x)) ::: If the restaurant is listed in Yelp’s recommendations, then the restaurant does not receive many negative reviews.
∀x (Rating(x, y) ∧ y > 9 → Listed(x)) ::: All restaurants with a rating greater than 9 are listed in Yelp’s recommendations.
∃x (¬TakeOut(x) ∧ NegativeReviews(x)) ::: Some restaurants that do not provide take-out service receive many negative reviews.
∀x (Popular(x) → (Rating(x, y) ∧ y > 9)) ::: All restaurants that are popular among local residents have ratings greater than 9.
Rating(subway, y) ∧ y > 9 ∨ Popular(subway) ::: Subway has a rating greater than 9 or is popular among local residents.
# Conclusion:
TakeOut(subway) ∧ ¬NegativeReviews(subway) ::: Subway provides take-out service and does not receive many negative reviews. FALSE
>>> Error Message:
Parsing Error
>>> Correct Program:
# Predicates:
Listed(x) ::: x is listed in Yelp’s recommendations.
NegativeReviews(x) ::: x receives many negative reviews.
TakeOut(x) ::: x provides take-out service.
Popular(x) ::: x is popular among local residents.
GreaterThanNine(x) ::: x has a rating greater than 9.
# Premises:
∀x (Listed(x) → ¬NegativeReviews(x)) ::: If the restaurant is listed in Yelp’s recommendations, then the restaurant does not receive many negative reviews.
∀x (GreaterThanNine(x) → Listed(x)) ::: All restaurants with a rating greater than 9 are listed in Yelp’s recommendations.
∃x (¬TakeOut(x) ∧ NegativeReviews(x)) ::: Some restaurants that do not provide take-out service receive many negative reviews.
∀x (Popular(x) → GreaterThanNine(x)) ::: All restaurants that are popular among local residents have ratings greater than 9.
GreaterThanNine(subway) ∨ Popular(subway) ::: Subway has a rating greater than 9 or is popular among local residents.
# Conclusion:
TakeOut(subway) ∧ ¬NegativeReviews(subway) ::: Subway provides take-out service and does not receive many negative reviews. FALSE
------

DO NOT write the # Problem, # Predicates, or # Premises sections!!!
Here is the program you need to work with:
>>> Initial Program:
{PROGRAM}
>>> Error Message:
{ERROR_MESSAGE}
>>> Corrected Program:

"""



########################################################

PROGRAM_CROSSOVER_PROMPT = FOLIO_NOTATION_SUMMARY + """
You are merging **two** independently written first-order logic encodings of the same
problem scenario into a single, higher-quality child program.

================  CONTEXT  ================
--- SCENARIO INFORMATION ---
{PROBLEM}

--- PARENT A ---
{parent_a}

--- PARENT B ---
{parent_b}
===========================================

TASK
----
1. Combine the strengths of both parents: keep logically correct rules,
   deduplicate or reconcile conflicting clauses.
2. Ensure you keep the same format, including # Predicates: and # Premises: sections.
3. Do not write any # Problem, # Question, or # Conclusion sections.
4. Generally keep the same vocabulary.
"""



# † Variables injected: {contract_text}, {program}
PROGRAM_MUTATION_PROMPT = """
You are improving a first-order logic encoding of the problem scenario shown below.
Make edits that fix bugs, add missing edge-cases, or simplify logic.

================  CONTEXT  ================
--- SCENARIO INFORMATION ---
{PROBLEM}

--- CURRENT PROGRAM ---
{program}
===========================================

TASK
----
1. Your task is to write a new program that is different from this program, which satisfies the same problem.
2. Ensure you keep the correct format, including # Predicates: and # Premises: sections.
3. Do not write any # Problem, # Question, or # Conclusion sections.
4. Generally keep the same vocabulary.
"""

# # † Variables injected: {contract_text}, {test}
# TEST_MUTATION_PROMPT = """
# You are mutating ONE first-order-logic test case (question & conclusion) for the problem scenario below in order
# to explore a *different* question while keeping the same vocabulary.

# ================  CONTEXT  ================
# --- PROBLEM SCENARIO ---
# {contract_text}

# --- ORIGINAL TEST ---
# {test}
# ===========================================

# GUIDELINES
# ----------
# 1. Your task is to write a new test that is different from this test, which satisfies the same problem.
# 2. Ideally this new test explores a different aspect of the problem, or an edge-case.
# 3. Ensure you keep the correct format, including # Question: and # Conclusion: sections.
# 4. Do not write any # Problem, # Predicates, or # Premises sections.
# 5. Generally keep the same vocabulary.
# 6. Do not use the same question as the original test.
# """




FOLIO_SINGLE_TEST_GENERATION = FOLIO_NOTATION_SUMMARY + """
Given a problem description and a question. The task is to parse the problem, create a new question based on that problem, and translate it into first-order logic.

Your job SPECIFICALLY is to create a new question based on the problem, and generate the Conclusion section in first-order logic that can be answered with the predicates and premises that will be generated separately.
You do not need to write the # Problem, # Predicates, or # Premises sections.
You should only write the # Question and # Conclusion sections.

I will provide you with some examples:
------
# Problem:
All people who regularly drink coffee are dependent on caffeine. People either regularly drink coffee or joke about being addicted to caffeine. No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# Question:
Based on the above information, is the following statement true, false, or uncertain? Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug.
Based on the above information, is the following statement true, false, or uncertain? If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee.
###
# Predicates:
Dependent(x) ::: x is a person dependent on caffeine.
Drinks(x) ::: x regularly drinks coffee.
Jokes(x) ::: x jokes about being addicted to caffeine.
Unaware(x) ::: x is unaware that caffeine is a drug.
Student(x) ::: x is a student.
# Premises:
∀x (Drinks(x) → Dependent(x)) ::: All people who regularly drink coffee are dependent on caffeine.
∀x (Drinks(x) ⊕ Jokes(x)) ::: People either regularly drink coffee or joke about being addicted to caffeine.
∀x (Jokes(x) → ¬Unaware(x)) ::: No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. 
(Student(rina) ∧ Unaware(rina)) ⊕ ¬(Student(rina) ∨ Unaware(rina)) ::: Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. 
¬(Dependent(rina) ∧ Student(rina)) → (Dependent(rina) ∧ Student(rina)) ⊕ ¬(Dependent(rina) ∨ Student(rina)) ::: If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
# Conclusion:
Jokes(rina) ⊕ Unaware(rina) ::: Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug. TRUE
((Jokes(rina) ∧ Unaware(rina)) ⊕ ¬(Jokes(rina) ∨ Unaware(rina))) → (Jokes(rina) ∧ Drinks(rina)) ::: If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee. FALSE
------
# Problem:
Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music. Any choral conductor is a musician. Some musicians love music. Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# Question:
Based on the above information, is the following statement true, false, or uncertain? Miroslav Venhoda loved music.
Based on the above information, is the following statement true, false, or uncertain? A Czech person wrote a book in 1946.
Based on the above information, is the following statement true, false, or uncertain? No choral conductor specialized in the performance of Renaissance.
###
# Predicates:
Czech(x) ::: x is a Czech person.
ChoralConductor(x) ::: x is a choral conductor.
Musician(x) ::: x is a musician.
Love(x, y) ::: x loves y.
Author(x, y) ::: x is the author of y.
Book(x) ::: x is a book.
Publish(x, y) ::: x is published in year y.
Specialize(x, y) ::: x specializes in y.
# Premises:
Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
# Conclusion:
Love(miroslav, music) ::: Miroslav Venhoda loved music. UNKNOWN
∃y ∃x (Czech(x) ∧ Author(x, y) ∧ Book(y) ∧ Publish(y, year1946)) ::: A Czech person wrote a book in 1946. FALSE
¬∃x (ChoralConductor(x) ∧ Specialize(x, renaissance)) ::: No choral conductor specialized in the performance of Renaissance. UNKNOWN
------
{PRELUDE}
{PROGRAM}
{TESTS}


At the end of the conclusion, in the comment (i.e. after the ':::') write at the end of the comment whether the conclusion is TRUE, FALSE, or UNKNOWN.
^^^ This is very important!

Write a SINGLE new # Question and # Conclusion section based on the problem below.

Here is the problem you need to work with:

# Problem:
{PROBLEM}


Write the # Question: and # Conclusion: sections here:
"""
