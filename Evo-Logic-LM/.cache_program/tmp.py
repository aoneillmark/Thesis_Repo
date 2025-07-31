from z3 import *

students_sort, (George, Helen, Irving, Kyle, Lenore, Nina, Olivia, Robert) = EnumSort('students', ['George', 'Helen', 'Irving', 'Kyle', 'Lenore', 'Nina', 'Olivia', 'Robert'])
days_sort, (Monday, Tuesday, Wednesday) = EnumSort('days', ['Monday', 'Tuesday', 'Wednesday'])
times_sort, (Morning, Afternoon) = EnumSort('times', ['Morning', 'Afternoon'])
students = [George, Helen, Irving, Kyle, Lenore, Nina, Olivia, Robert]
days = [Monday, Tuesday, Wednesday]
times = [Morning, Afternoon]
report = Function('report', students_sort, days_sort, times_sort, BoolSort())

pre_conditions = []
s = Const('s', students_sort)
pre_conditions.append(ForAll([s], Sum([d:days, t:times], Ite(report(s, d, t), 1, 0)) <= 1))
d = Const('d', days_sort)
pre_conditions.append(ForAll([d], Sum([s:students, t:times], Ite(report(s, d, t), 1, 0)) == 2))
s = Const('s', students_sort)
pre_conditions.append(ForAll([s], Implies(report(s, Tuesday, Morning) or report(s, Tuesday, Afternoon), s == George or s == Olivia or s == Robert or s == Helen or s == Irving or s == Kyle or s == Lenore or s == Nina)))
s = Const('s', students_sort)
pre_conditions.append(ForAll([s], Implies(report(s, Monday, Afternoon) or report(s, Tuesday, Afternoon) or report(s, Wednesday, Afternoon), s != Olivia and s != Robert)))
s = Const('s', students_sort)
d = Const('d', days_sort)
t = Const('t', times_sort)
pre_conditions.append(ForAll([s, d, t], Implies(report(s, d, t), And(s != Nina, Not(report(Helen, NextDay(d), Morning) or report(Helen, NextDay(d), Afternoon) or report(Irving, NextDay(d), Morning) or report(Irving, NextDay(d), Afternoon))) or (s == Nina and d == Wednesday))))
s = Const('s', students_sort)
d = Const('d', days_sort)
pre_conditions.append(ForAll([s, d], And(Implies(report(s, d, Morning), s != George), Implies(report(s, d, Afternoon), s != George))))
s = Const('s', students_sort)
pre_conditions.append(ForAll([s], Sum([d:days, t:times], Ite(report(s, d, t), 1, 0)) <= 1))
d = Const('d', days_sort)
pre_conditions.append(ForAll([d], Sum([s:students, t:times], Ite(report(s, d, t), 1, 0)) == 2))
s = Const('s', students_sort)
pre_conditions.append(ForAll([s], Implies(report(s, Tuesday, Morning) or report(s, Tuesday, Afternoon), s == George or s == Olivia or s == Robert or s == Helen or s == Irving or s == Kyle or s == Lenore or s == Nina)))
s = Const('s', students_sort)
pre_conditions.append(ForAll([s], Implies(report(s, Monday, Afternoon) or report(s, Tuesday, Afternoon) or report(s, Wednesday, Afternoon), s != Olivia and s != Robert)))
s = Const('s', students_sort)
d = Const('d', days_sort)
t = Const('t', times_sort)
pre_conditions.append(ForAll([s, d, t], Implies(report(s, d, t), And(s != Nina, Not(report(Helen, NextDay(d), Morning) or report(Helen, NextDay(d), Afternoon) or report(Irving, NextDay(d), Morning) or report(Irving, NextDay(d), Afternoon))) or (s == Nina and d == Wednesday))))
s = Const('s', students_sort)
d = Const('d', days_sort)
pre_conditions.append(ForAll([s, d], And(Implies(report(s, d, Morning), s != George), Implies(report(s, d, Afternoon), s != George))))

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


if is_valid(report(Nina, Tue, Morning) or report(Nina, Tue, Afternoon)): print('(A)')
if is_valid(report(Helen, Mon, Morning) or report(Helen, Mon, Afternoon)): print('(B)')
if is_valid(report(Robert, Mon, Morning) or report(Robert, Mon, Afternoon) or report(Robert, Tue, Morning) or report(Robert, Tue, Afternoon) or report(Robert, Wed, Morning) or report(Robert, Wed, Afternoon)): print('(C)')
if is_valid(report(Irving, Wed, Morning) or report(Irving, Wed, Afternoon)): print('(D)')
if is_valid(report(George, Mon, Morning) or report(George, Mon, Afternoon)): print('(E)')