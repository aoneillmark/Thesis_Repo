from z3 import *

boys_sort, (Fred, Juan, Marc, Paul) = EnumSort('boys', ['Fred', 'Juan', 'Marc', 'Paul'])
girls_sort, (Nita, Rachel, Trisha) = EnumSort('girls', ['Nita', 'Rachel', 'Trisha'])
lockers_sort = IntSort()
locker_sort = IntSort()
[children_sort], IntSort( = Ints('[children_sort] IntSort(')
locker = [[children_sort], IntSort(]
boys = [Fred, Juan, Marc, Paul]
girls = [Nita, Rachel, Trisha]
children_sort = [Fred, Juan, Marc, Paul, Nita, Rachel, Trisha]
lockers = [1, 2, 3, 4, 5]
shares = Function('shares', [children_sort]_sort, BoolSort()_sort)
shared_with = Function('shared_with', [children_sort]_sort, children_sort_sort)

pre_conditions = []
c = Const('c', children_sort_sort)
pre_conditions.append(ForAll([c], And(locker(c) >= 1, locker(c) <= 5)))
pre_conditions.append(And([Sum([locker(c) == l for c in children_sort]) <= 2 for l in lockers]))
c = Const('c', children_sort_sort)
pre_conditions.append(ForAll([c], Sum([locker(c2) == locker(c) for c2 in children_sort]) == If(shares(c), 2, 1)))
c1 = Const('c1', children_sort_sort)
c2 = Const('c2', children_sort_sort)
pre_conditions.append(ForAll([c1, c2], Implies(And(c1 != c2, locker(c1) == locker(c2)), Or(And(c1 in boys, c2 in girls), And(c1 in girls, c2 in boys)))))
g = Const('g', girls_sort)
b = Const('b', boys_sort)
pre_conditions.append(ForAll([g, b], Implies(And(shares(g), shares(b), locker(g) == locker(b)), Or(And(g in girls, b in boys), And(g in boys, b in girls)))))
c = Const('c', children_sort_sort)
pre_conditions.append(ForAll([c], Implies(shares(c), And(Sum([And(locker(c2) == locker(c), c2 in boys) for c2 in children_sort]) == 1, Sum([And(locker(c2) == locker(c), c2 in girls) for c2 in children_sort]) == 1))))
c = Const('c', children_sort_sort)
pre_conditions.append(ForAll([c], And(locker(c) >= 1, locker(c) <= 5)))
pre_conditions.append(And([Sum([locker(c) == l for c in children_sort]) <= 2 for l in lockers]))
c = Const('c', children_sort_sort)
pre_conditions.append(ForAll([c], Sum([locker(c2) == locker(c) for c2 in children_sort]) == If(shares(c), 2, 1)))
c1 = Const('c1', children_sort_sort)
c2 = Const('c2', children_sort_sort)
pre_conditions.append(ForAll([c1, c2], Implies(And(c1 != c2, locker(c1) == locker(c2)), Or(And(c1 in boys, c2 in girls), And(c1 in girls, c2 in boys)))))
g = Const('g', girls_sort)
b = Const('b', boys_sort)
pre_conditions.append(ForAll([g, b], Implies(And(shares(g), shares(b), locker(g) == locker(b)), Or(And(g in girls, b in boys), And(g in boys, b in girls)))))
c = Const('c', children_sort_sort)
pre_conditions.append(ForAll([c], Implies(shares(c), And(Sum([And(locker(c2) == locker(c), c2 in boys) for c2 in children_sort]) == 1, Sum([And(locker(c2) == locker(c), c2 in girls) for c2 in children_sort]) == 1))))

def is_valid(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(Not(option_constraints))
    return solver.check() == unsat

def is_unsat(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(option_constraints)
    return solver.check() == unsat

def is_sat(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(option_constraints)
    return solver.check() == sat

def is_accurate_list(option_constraints):
    return is_valid(Or(option_constraints)) and all([is_sat(c) for c in option_constraints])

def is_exception(x):
    return not x


if is_valid(shared(Juan, Nita)): print('(A)')
if is_valid(locker(Rachel) == 1): print('(B)')
if is_valid(Abs(locker(Nita) - locker(Trisha)) == 1): print('(C)')
if is_valid(shared(Fred, Paul)): print('(D)')
if is_valid(locker(Rachel) == 5): print('(E)')