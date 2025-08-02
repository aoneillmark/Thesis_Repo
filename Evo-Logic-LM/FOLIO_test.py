from fol_solver.prover9_solver import FOL_Prover9_Program



if __name__ == "__main__":
    # Test with a simple True case
    # simple_logic = """# Premises:
    # ∀x (Human(x) → Mortal(x)) ::: All humans are mortal.
    # Human(socrates) ::: Socrates is human.
    # # Conclusion:
    # Mortal(socrates) ::: Socrates is mortal."""

#     simple_logic = """
# # Question
# Based on the above information, is the following statement true, false, or uncertain? Bonnie attends and is very engaged with school events.

# # Predicates
# Performs(x) ::: x performs in school talent shows often.
# Attends(x) ::: x attends school events.
# Engaged(x) ::: x is very engaged with school events.
# Inactive(x) ::: x is an inactive member of their community.
# Disinterested(x) ::: x is a disinterested member of their community.
# Chaperone(x) ::: x chaperones high school dances.
# Student(x) ::: x is a student who attends the school.
# YoungChild(x) ::: x is a young child.
# Teenager(x) ::: x is a teenager.
# FurtherAcademics(x) ::: x wishes to further their academic careers and educational opportunities.

# # Premises
# ∀x (Performs(x) → (Attends(x) ∧ Engaged(x))) ::: If people perform in school talent shows often, then they attend and are very engaged with school events.
# ∀x (Performs(x) ⊕ (Inactive(x) ∧ Disinterested(x))) ::: People either perform in school talent shows often or are inactive and disinterested members of their community.
# ∀x (Chaperone(x) → ¬Student(x)) ::: If people chaperone high school dances, then they are not students who attend the school.
# ∀x ((Inactive(x) ∧ Disinterested(x)) → Chaperone(x)) ::: All people who are inactive and disinterested members of their community chaperone high school dances.
# ∀x ((YoungChild(x) ∨ Teenager(x)) ∧ FurtherAcademics(x) → Student(x)) ::: All young children and teenagers who wish to further their academic careers and educational opportunities are students who attend the school.

# # Conclusion:
# Attends(bonnie) ∧ Engaged(bonnie) ::: Bonnie attends and is very engaged with school events. UNKNOWN
# """

#     simple_logic = """
# # Question:
# Based on the above information, is the following statement true, false, or uncertain? Bonnie is a student who attends the school.

# # Predicates:
# Perform(x) ::: x performs in school talent shows often.
# Attend(x) ::: x attends school events.
# Engaged(x) ::: x is very engaged with school events.
# Inactive(x) ::: x is an inactive member of their community.
# Disinterested(x) ::: x is a disinterested member of their community.
# Chaperone(x) ::: x chaperones high school dances.
# Student(x) ::: x is a student who attends the school.
# Young(x) ::: x is a young child or teenager.
# FurtherAcademic(x) ::: x wishes to further their academic careers and educational opportunities.

# # Premises:
# ∀x (Perform(x) → (Attend(x) ∧ Engaged(x))) ::: If people perform in school talent shows often, then they attend and are very engaged with school events.
# ∀x (Perform(x) ⊕ (Inactive(x) ∧ Disinterested(x))) ::: People either perform in school talent shows often or are inactive and disinterested members of their community.
# ∀x (Chaperone(x) → ¬Student(x)) ::: If people chaperone high school dances, then they are not students who attend the school.
# ∀x ((Inactive(x) ∧ Disinterested(x)) → Chaperone(x)) ::: All people who are inactive and disinterested members of their community chaperone high school dances.
# ∀x ((Young(x) ∧ FurtherAcademic(x)) → Student(x)) ::: All young children and teenagers who wish to further their academic careers and educational opportunities are students who attend the school.
# (Attend(bonnie) ∧ Engaged(bonnie)) ⊕ ¬(Attend(bonnie) ∨ Engaged(bonnie)) ::: Bonnie either both attends and is very engaged with school events and is a student who attends the school, or she neither attends and is very engaged with school events nor is a student who attends the school.

# # Conclusion:
# Student(bonnie) ::: Bonnie is a student who attends the school. UNKNOWN
# """


    simple_logic = """
# Question:
Based on the above information, is the following statement true, false, or uncertain? If Bonnie is inactive and disinterested in her community, then she is a student who attends the school.

# Predicates:
Perform(x) ::: x performs in school talent shows often.
Attend(x) ::: x attends school events.
Engaged(x) ::: x is very engaged with school events.
Inactive(x) ::: x is an inactive member of their community.
Disinterested(x) ::: x is a disinterested member of their community.
Chaperone(x) ::: x chaperones high school dances.
Student(x) ::: x is a student who attends the school.
YoungChildOrTeenager(x) ::: x is a young child or teenager.
FurtherAcademicCareers(x) ::: x wishes to further their academic careers.
FurtherEducationalOpportunities(x) ::: x wishes to further their educational opportunities.

# Premises:
∀x (Perform(x) → (Attend(x) ∧ Engaged(x))) ::: If people perform in school talent shows often, then they attend and are very engaged with school events.
∀x (Perform(x) ⊕ (Inactive(x) ∧ Disinterested(x))) ::: People either perform in school talent shows often or are inactive and disinterested members of their community.
∀x (Chaperone(x) → ¬Student(x)) ::: If people chaperone high school dances, then they are not students who attend the school.
∀x ((Inactive(x) ∧ Disinterested(x)) → Chaperone(x)) ::: All people who are inactive and disinterested members of their community chaperone high school dances.
∀x ((YoungChildOrTeenager(x) ∧ FurtherAcademicCareers(x) ∧ FurtherEducationalOpportunities(x)) → Student(x)) ::: All young children and teenagers who wish to further their academic careers and educational opportunities are students who attend the school.
(Attend(bonnie) ∧ Engaged(bonnie)) ⊕ ¬(Attend(bonnie) ∧ Engaged(bonnie)) ::: Bonnie either both attends and is very engaged with school events and is a student who attends the school, or she neither attends and is very engaged with school events nor is a student who attends the school.

# Conclusion:
Inactive(bonnie) → Student(bonnie) ::: If Bonnie is inactive and disinterested in her community, then she is a student who attends the school. UNKNOWN
"""


    prover9_program = FOL_Prover9_Program(simple_logic)
    answer, error_message = prover9_program.execute_program()
    print(prover9_program.syntax_error)
    print(f"Simple test result: {answer}")