from collections import OrderedDict
from code_translator import *
import subprocess
from subprocess import check_output
from os.path import join
import os

class LSAT_Z3_Program:
    def __init__(self, logic_program:str, dataset_name:str) -> None:
        self.logic_program = logic_program
        self.dataset_name = dataset_name
        self.error_message = None  # Add this line
        
        # create the folder to save the program first
        cache_dir = os.path.join(os.path.dirname(__file__), '.cache_program')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.cache_dir = cache_dir
        
        try:
            self.parse_logic_program()
            self.standard_code = self.to_standard_code()
            self.flag = True
        except Exception as e:
            print(f"Error parsing logic program: {e}")
            self.error_message = str(e)  # Store the error message
            self.standard_code = None
            self.flag = False
            return
    
    def parse_logic_program(self):
        # split the logic program into different parts
        lines = [x for x in self.logic_program.splitlines() if not x.strip() == ""]

        option_start_index = lines.index("# Options")
        decleration_start_index = lines.index("# Declarations")
        constraint_start_index = lines.index("# Constraints")
 
        # declaration_statements = lines[decleration_start_index + 1:constraint_start_index]
        # constraint_statements = lines[constraint_start_index + 1:option_start_index]
        # option_statements = lines[option_start_index + 1:]

        # Reorder such that options is first
        option_statements = lines[option_start_index + 1:decleration_start_index]
        declaration_statements = lines[decleration_start_index + 1:constraint_start_index]
        constraint_statements = lines[constraint_start_index + 1:]

        try:
            (self.declared_enum_sorts, self.declared_int_sorts, self.declared_lists, self.declared_functions, self.variable_constrants) = self.parse_declaration_statements(declaration_statements)

            self.constraints = [x.split(':::')[0].strip() for x in constraint_statements]
            self.options = [x.split(':::')[0].strip() for x in option_statements if not x.startswith("Question :::")]
        except Exception as e:
            return False
        
        return True

    def __repr__(self):
        return f"LSATSatProblem:\n\tDeclared Enum Sorts: {self.declared_enum_sorts}\n\tDeclared Lists: {self.declared_lists}\n\tDeclared Functions: {self.declared_functions}\n\tConstraints: {self.constraints}\n\tOptions: {self.options}"

    def parse_declaration_statements(self, declaration_statements):
        enum_sort_declarations = OrderedDict()
        int_sort_declarations = OrderedDict()
        function_declarations = OrderedDict()
        pure_declaration_statements = [x for x in declaration_statements if "Sort" in x or "Function" in x]
        variable_constrant_statements = [x for x in declaration_statements if not "Sort" in x and not "Function" in x]
        for s in pure_declaration_statements:
            if "EnumSort" in s:
                sort_name = s.split("=")[0].strip()
                sort_member_str = s.split("=")[1].strip()[len("EnumSort("):-1]
                sort_members = [x.strip() for x in sort_member_str[1:-1].split(",")]
                enum_sort_declarations[sort_name] = sort_members
            elif "IntSort" in s:
                sort_name = s.split("=")[0].strip()
                sort_member_str = s.split("=")[1].strip()[len("IntSort("):-1]
                sort_members = [x.strip() for x in sort_member_str[1:-1].split(",")]
                int_sort_declarations[sort_name] = sort_members
            elif "Function" in s:
                function_name = s.split("=")[0].strip()
                if "->" in s and "[" not in s:
                    function_args_str = s.split("=")[1].strip()[len("Function("):]
                    function_args_str = function_args_str.replace("->", ",").replace("(", "").replace(")", "")
                    function_args = [x.strip() for x in function_args_str.split(",")]
                    function_declarations[function_name] = function_args
                elif "->" in s and "[" in s:
                    function_args_str = s.split("=")[1].strip()[len("Function("):-1]
                    function_args_str = function_args_str.replace("->", ",").replace("[", "").replace("]", "")
                    function_args = [x.strip() for x in function_args_str.split(",")]
                    function_declarations[function_name] = function_args
                else:
                    # legacy way
                    function_args_str = s.split("=")[1].strip()[len("Function("):-1]
                    function_args = [x.strip() for x in function_args_str.split(",")]
                    function_declarations[function_name] = function_args
            else:
                raise RuntimeError("Unknown declaration statement: {}".format(s))

        declared_enum_sorts = OrderedDict()
        declared_lists = OrderedDict()
        self.declared_int_lists = OrderedDict()

        declared_functions = function_declarations
        already_declared = set()
        for name, members in enum_sort_declarations.items():
            # all contained by other enum sorts
            if all([x not in already_declared for x in members]):
                declared_enum_sorts[name] = members
                already_declared.update(members)
            declared_lists[name] = members

        for name, members in int_sort_declarations.items():
            self.declared_int_lists[name] = members
            # declared_lists[name] = members

        return declared_enum_sorts, int_sort_declarations, declared_lists, declared_functions, variable_constrant_statements
    
    def to_standard_code(self):
        declaration_lines = []
        # translate enum sorts
        for name, members in self.declared_enum_sorts.items():
            declaration_lines += CodeTranslator.translate_enum_sort_declaration(name, members)

        # translate int sorts
        for name, members in self.declared_int_sorts.items():
            declaration_lines += CodeTranslator.translate_int_sort_declaration(name, members)

        # translate lists
        for name, members in self.declared_lists.items():
            declaration_lines += CodeTranslator.translate_list_declaration(name, members)

        scoped_list_to_type = {}
        for name, members in self.declared_lists.items():
            if all(x.isdigit() for x in members):
                scoped_list_to_type[name] = CodeTranslator.ListValType.INT
            else:
                scoped_list_to_type[name] = CodeTranslator.ListValType.ENUM

        for name, members in self.declared_int_lists.items():
            scoped_list_to_type[name] = CodeTranslator.ListValType.INT
        
        # translate functions
        for name, args in self.declared_functions.items():
            declaration_lines += CodeTranslator.translate_function_declaration(name, args)

        pre_condidtion_lines = []

        for constraint in self.constraints:
            pre_condidtion_lines += CodeTranslator.translate_constraint(constraint, scoped_list_to_type)

        # additional function scope control
        for name, args in self.declared_functions.items():
            if args[-1] in scoped_list_to_type and scoped_list_to_type[args[-1]] == CodeTranslator.ListValType.INT:
                # FIX
                if args[-1] in self.declared_int_lists:
                    continue
                
                list_range = [int(x) for x in self.declared_lists[args[-1]]]
                assert list_range[-1] - list_range[0] == len(list_range) - 1
                scoped_vars = [x[0] + str(i) for i, x in enumerate(args[:-1])]
                func_call = f"{name}({', '.join(scoped_vars)})"

                additional_cons = "ForAll([{}], And({} <= {}, {} <= {}))".format(
                    ", ".join([f"{a}:{b}" for a, b in zip(scoped_vars, args[:-1])]),
                    list_range[0], func_call, func_call, list_range[-1]
                )
                pre_condidtion_lines += CodeTranslator.translate_constraint(additional_cons, scoped_list_to_type)


        for constraint in self.constraints:
            pre_condidtion_lines += CodeTranslator.translate_constraint(constraint, scoped_list_to_type)

        # each block should express one option
        option_blocks = [CodeTranslator.translate_constraint(option, scoped_list_to_type) for option in self.options]

        return CodeTranslator.assemble_standard_code(declaration_lines, pre_condidtion_lines, option_blocks)
    
    # def execute_program(self):
    #     filename = join(self.cache_dir, f'tmp.py')
    #     with open(filename, "w") as f:
    #         f.write(self.standard_code)
    #     try:
    #         output = check_output(["python", filename], stderr=subprocess.STDOUT, timeout=1.0)
    #     except subprocess.CalledProcessError as e:
    #         outputs = e.output.decode("utf-8").strip().splitlines()[-1]
    #         return None, outputs
    #     except subprocess.TimeoutExpired:
    #         return None, 'TimeoutError'
    #     output = output.decode("utf-8").strip()
    #     result = output.splitlines()
    #     if len(result) == 0:
    #         return None, 'No Output'
        
    #     return result, ""
    
    def execute_program(self):
        filename = join(self.cache_dir, f'tmp.py')
        with open(filename, "w") as f:
            f.write(self.standard_code)
        try:
            import sys
            # Use the same Python interpreter that's currently running
            output = check_output([sys.executable, filename], stderr=subprocess.STDOUT, timeout=10.0)
        except subprocess.CalledProcessError as e:
            outputs = e.output.decode("utf-8").strip()
            return None, outputs
        except subprocess.TimeoutExpired:
            return None, 'TimeoutError'
        except Exception as e:
            return None, str(e)
        output = output.decode("utf-8").strip()
        result = output.splitlines()
        if len(result) == 0:
            return None, 'No Output'
        
        return result, ""
    
    def answer_mapping(self, answer):
        if answer is None:
            return "No valid answer found"
        
        mapping = {'(A)': 'A', '(B)': 'B', '(C)': 'C', '(D)': 'D', '(E)': 'E',
                'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E'}
        
        try:
            return mapping[answer[0].strip()]
        except (IndexError, KeyError, AttributeError):
            return "Invalid answer format"


# logic_program = '''# Declarations
# people = EnumSort([Vladimir, Wendy])
# meals = EnumSort([breakfast, lunch, dinner, snack])
# foods = EnumSort([fish, hot_cakes, macaroni, omelet, poached_eggs])
# eats = Function([people, meals] -> [foods])

# # Constraints
# ForAll([m:meals], eats(Vladimir, m) != eats(Wendy, m)) ::: At no meal does Vladimir eat the same kind of food as Wendy
# ForAll([p:people, f:foods], Count([m:meals], eats(p, m) == f) <= 1) ::: Neither of them eats the same kind of food more than once during the day
# ForAll([p:people], Or(eats(p, breakfast) == hot_cakes, eats(p, breakfast) == poached_eggs, eats(p, breakfast) == omelet)) ::: For breakfast, each eats exactly one of the following: hot cakes, poached eggs, or omelet
# ForAll([p:people], Or(eats(p, lunch) == fish, eats(p, lunch) == hot_cakes, eats(p, lunch) == macaroni, eats(p, lunch) == omelet)) ::: For lunch, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
# ForAll([p:people], Or(eats(p, dinner) == fish, eats(p, dinner) == hot_cakes, eats(p, dinner) == macaroni, eats(p, dinner) == omelet)) ::: For dinner, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
# ForAll([p:people], Or(eats(p, snack) == fish, eats(p, snack) == omelet)) ::: For a snack, each eats exactly one of the following: fish or omelet
# eats(Wendy, lunch) == omelet ::: Wendy eats an omelet for lunch

# # Options
# Question ::: Vladimir must eat which one of the following foods?
# is_valid(Exists([m:meals], eats(Vladimir, m) == fish)) ::: (A)
# is_valid(Exists([m:meals], eats(Vladimir, m) == hot_cakes)) ::: (B)
# is_valid(Exists([m:meals], eats(Vladimir, m) == macaroni)) ::: (C)
# is_valid(Exists([m:meals], eats(Vladimir, m) == omelet)) ::: (D)
# is_valid(Exists([m:meals], eats(Vladimir, m) == poached_eggs)) ::: (E)'''



# logic_program = '''# Options
# Question ::: Vladimir must eat which one of the following foods?
# is_valid(Exists([m:meals], eats(Vladimir, m) == fish)) ::: (A)
# is_valid(Exists([m:meals], eats(Vladimir, m) == hot_cakes)) ::: (B)
# is_valid(Exists([m:meals], eats(Vladimir, m) == macaroni)) ::: (C)
# is_valid(Exists([m:meals], eats(Vladimir, m) == omelet)) ::: (D)
# is_valid(Exists([m:meals], eats(Vladimir, m) == poached_eggs)) ::: (E)
    
# # Declarations
# people = EnumSort([Vladimir, Wendy])
# meals = EnumSort([breakfast, lunch, dinner, snack])
# foods = EnumSort([fish, hot_cakes, macaroni, omelet, poached_eggs])
# eats = Function([people, meals] -> [foods])

# # Constraints
# ForAll([m:meals], eats(Vladimir, m) != eats(Wendy, m)) ::: At no meal does Vladimir eat the same kind of food as Wendy
# ForAll([p:people, f:foods], Count([m:meals], eats(p, m) == f) <= 1) ::: Neither of them eats the same kind of food more than once during the day
# ForAll([p:people], Or(eats(p, breakfast) == hot_cakes, eats(p, breakfast) == poached_eggs, eats(p, breakfast) == omelet)) ::: For breakfast, each eats exactly one of the following: hot cakes, poached eggs, or omelet
# ForAll([p:people], Or(eats(p, lunch) == fish, eats(p, lunch) == hot_cakes, eats(p, lunch) == macaroni, eats(p, lunch) == omelet)) ::: For lunch, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
# ForAll([p:people], Or(eats(p, dinner) == fish, eats(p, dinner) == hot_cakes, eats(p, dinner) == macaroni, eats(p, dinner) == omelet)) ::: For dinner, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
# ForAll([p:people], Or(eats(p, snack) == fish, eats(p, snack) == omelet)) ::: For a snack, each eats exactly one of the following: fish or omelet
# eats(Wendy, lunch) == omelet ::: Wendy eats an omelet for lunch'''


logic_program = """

# Options
Question ::: Which of the following assignments of students to report slots satisfies all conditions?
is_sat(And(report_day(George) == Monday, report_time(George) == Morning, report_day(Helen) == Monday, report_time(Helen) == Afternoon, report_day(Irving) == Tuesday, report_time(Irving) == Morning, report_day(Lenore) == Tuesday, report_time(Lenore) == Afternoon, report_day(Nina) == Wednesday, report_time(Nina) == Morning, report_day(Olivia) == Wednesday, report_time(Olivia) == Afternoon)) ::: (A)
is_sat(And(report_day(George) == Monday, report_time(George) == Morning, report_day(Lenore) == Monday, report_time(Lenore) == Afternoon, report_day(Helen) == Tuesday, report_time(Helen) == Morning, report_day(Irving) == Tuesday, report_time(Irving) == Afternoon, report_day(Nina) == Wednesday, report_time(Nina) == Morning, report_day(Robert) == Wednesday, report_time(Robert) == Afternoon)) ::: (B)
is_sat(And(report_day(George) == Monday, report_time(George) == Morning, report_day(Nina) == Monday, report_time(Nina) == Afternoon, report_day(Helen) == Tuesday, report_time(Helen) == Morning, report_day(Irving) == Tuesday, report_time(Irving) == Afternoon, report_day(Lenore) == Wednesday, report_time(Lenore) == Morning, report_day(Olivia) == Wednesday, report_time(Olivia) == Afternoon)) ::: (C) *
is_sat(And(report_day(George) == Monday, report_time(George) == Morning, report_day(Helen) == Monday, report_time(Helen) == Afternoon, report_day(Irving) == Tuesday, report_time(Irving) == Morning, report_day(Lenore) == Tuesday, report_time(Lenore) == Afternoon, report_day(Robert) == Wednesday, report_time(Robert) == Morning, report_day(Nina) == Wednesday, report_time(Nina) == Afternoon)) ::: (D)
is_sat(And(report_day(Helen) == Monday, report_time(Helen) == Morning, report_day(George) == Monday, report_time(George) == Afternoon, report_day(Irving) == Tuesday, report_time(Irving) == Morning, report_day(Lenore) == Tuesday, report_time(Lenore) == Afternoon, report_day(Nina) == Wednesday, report_time(Nina) == Morning, report_day(Olivia) == Wednesday, report_time(Olivia) == Afternoon)) ::: (E)

# Declarations
students = EnumSort([George, Helen, Irving, Kyle, Lenore, Nina, Olivia, Robert])
days = EnumSort([Monday, Tuesday, Wednesday])
times = EnumSort([Morning, Afternoon])
reports = Function('reports', students, ProductSort(days, times))
num_students_reporting = 6
num_days = 3
num_slots_per_day = 2
total_slots = num_days * num_slots_per_day

# Constraints
ForAll([s:students], Count([d:days, t:times], reports(s) == (d, t)) <= 1) ::: Each student reports at most once
ForAll([d:days, t:times], Count([s:students], reports(s) == (d, t)) == 1) ::: Exactly one student per slot
ForAll([s:students], Count([d:days, t:times], reports(s) == (d, t)) == 1) ::: Exactly six students will give oral reports
ForAll([s:students], Implies(Or(reports(s) == (Tuesday, Morning), reports(s) == (Tuesday, Afternoon)), s == George)) ::: Tuesday is the only day on which George can give a report. (This constraint implicitly handles that George must report, and only on Tuesday)
ForAll([s:students], Implies(Or(reports(s) == (Monday, Afternoon), reports(s) == (Tuesday, Afternoon), reports(s) == (Wednesday, Afternoon)), And(s != Olivia, s != Robert))) ::: Neither Olivia nor Robert can give an afternoon report.
ForAll([s:students], Implies(And(reports(s) == (Wednesday, Morning), s == Nina), And(Or(reports(Helen) == (Monday, Morning), reports(Helen) == (Monday, Afternoon), reports(Helen) == (Tuesday, Morning), reports(Helen) == (Tuesday, Afternoon)), And(Or(reports(Irving) == (Monday, Morning), reports(Irving) == (Monday, Afternoon), reports(Irving) == (Tuesday, Morning), reports(Irving) == (Tuesday, Afternoon)))))) ::: If Nina gives a report on Wednesday, then Helen and Irving must both give reports on Monday or Tuesday.
ForAll([s:students], Implies(And(reports(s) == (Monday, Morning), s == Nina), Implies(And(Or(reports(Helen) == (Tuesday, Morning), reports(Helen) == (Tuesday, Afternoon)), And(Or(reports(Irving) == (Tuesday, Morning), reports(Irving) == (Tuesday, Afternoon)))), True))) ::: If Nina gives a report on Monday, and Helen and Irving give reports on Tuesday, this is allowed.
ForAll([s:students], Implies(And(reports(s) == (Monday, Morning), s == Nina), Implies(And(Or(reports(Helen) == (Monday, Morning), reports(Helen) == (Monday, Afternoon)), And(Or(reports(Irving) == (Monday, Morning), reports(Irving) == (Monday, Afternoon)))), True))) ::: If Nina gives a report on Monday, and Helen and Irving give reports on Monday, this is allowed.
ForAll([s:students], Implies(And(reports(s) == (Tuesday, Morning), s == Nina), Implies(And(Or(reports(Helen) == (Wednesday, Morning), reports(Helen) == (Wednesday, Afternoon)), And(Or(reports(Irving) == (Wednesday, Morning), reports(Irving) == (Wednesday, Afternoon)))), True))) ::: If Nina gives a report on Tuesday, and Helen and Irving give reports on Wednesday, this is allowed.
ForAll([s:students], Implies(And(reports(s) == (Monday, Morning), s == Nina), Implies(And(Or(reports(Helen) == (Wednesday, Morning), reports(Helen) == (Wednesday, Afternoon)), And(Or(reports(Irving) == (Wednesday, Morning), reports(Irving) == (Wednesday, Afternoon)))), True))) ::: If Nina gives a report on Monday, and Helen and Irving give reports on Wednesday, this is allowed.
ForAll([s:students], Implies(And(reports(s) == (Tuesday, Morning), s == Nina), Implies(And(Or(reports(Helen) == (Wednesday, Morning), reports(Helen) == (Wednesday, Afternoon)), And(Or(reports(Irving) == (Wednesday, Morning), reports(Irving) == (Wednesday, Afternoon)))), True))) ::: If Nina gives a report on Tuesday, and Helen and Irving give reports on Wednesday, this is allowed.
ForAll([s:students], Implies(And(reports(s) == (Wednesday, Morning), s == Nina), True)) ::: If Nina reports on Wednesday, the condition about Helen and Irving giving reports on the next day is vacuously true.
ForAll([s:students], Implies(And(reports(s) == (Monday, Morning), s == Nina), And(Or(reports(Helen) == (Tuesday, Morning), reports(Helen) == (Tuesday, Afternoon)), And(Or(reports(Irving) == (Tuesday, Morning), reports(Irving) == (Tuesday, Afternoon)))))) ::: If Nina reports on Monday, then Helen and Irving must both give reports on Tuesday.
ForAll([s:students], Implies(And(reports(s) == (Tuesday, Morning), s == Nina), And(Or(reports(Helen) == (Wednesday, Morning), reports(Helen) == (Wednesday, Afternoon)), And(Or(reports(Irving) == (Wednesday, Morning), reports(Irving) == (Wednesday, Afternoon)))))) ::: If Nina reports on Tuesday, then Helen and Irving must both give reports on Wednesday.
ForAll([s:students], Implies(And(reports(s) == (Monday, Morning), s == Nina), And(Or(reports(Helen) == (Tuesday, Morning), reports(Helen) == (Tuesday, Afternoon)), And(Or(reports(Irving) == (Tuesday, Morning), reports(Irving) == (Tuesday, Afternoon)))))) ::: If Nina reports on Monday, then Helen and Irving must both give reports on Tuesday.
ForAll([s:students], Implies(And(reports(s) == (Tuesday, Morning), s == Nina), And(Or(reports(Helen) == (Wednesday, Morning), reports(Helen) == (Wednesday, Afternoon)), And(Or(reports(Irving) == (Wednesday, Morning), reports(Irving) == (Wednesday, Afternoon)))))) ::: If Nina reports on Tuesday, then Helen and Irving must both give reports on Wednesday.

"""



# if __name__=="__main__":

#     z3_program = LSAT_Z3_Program(logic_program, 'AR-LSAT')
#     print(z3_program.standard_code)

#     output, error_message = z3_program.execute_program()
#     print(output)
#     print(z3_program.answer_mapping(output))


if __name__=="__main__":
    z3_program = LSAT_Z3_Program(logic_program, 'AR-LSAT')
    
    if z3_program.standard_code is None:
        print("Failed to parse logic program")
    else:
        print(z3_program.standard_code)
        
        output, error_message = z3_program.execute_program()
        print("Output:", output)
        print("Error:", error_message)
        
        if output is not None:
            print("Answer:", z3_program.answer_mapping(output))
        else:
            print("No valid answer found")

# if __name__=="__main__":
#     logic_program = '''# Declarations
# people = EnumSort([Vladimir, Wendy])
# meals = EnumSort([breakfast, lunch, dinner, snack])
# foods = EnumSort([fish, hot_cakes, macaroni, omelet, poached_eggs])
# eats = Function([people, meals] -> [foods])

# # Constraints
# ForAll([m:meals], eats(Vladimir, m) != eats(Wendy, m)) ::: At no meal does Vladimir eat the same kind of food as Wendy
# ForAll([p:people, f:foods], Count([m:meals], eats(p, m) == f) <= 1) ::: Neither of them eats the same kind of food more than once during the day
# ForAll([p:people], Or(eats(p, breakfast) == hot_cakes, eats(p, breakfast) == poached_eggs, eats(p, breakfast) == omelet)) ::: For breakfast, each eats exactly one of the following: hot cakes, poached eggs, or omelet
# ForAll([p:people], Or(eats(p, lunch) == fish, eats(p, lunch) == hot_cakes, eats(p, lunch) == macaroni, eats(p, lunch) == omelet)) ::: For lunch, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
# ForAll([p:people], Or(eats(p, dinner) == fish, eats(p, dinner) == hot_cakes, eats(p, dinner) == macaroni, eats(p, dinner) == omelet)) ::: For dinner, each eats exactly one of the following: fish, hot cakes, macaroni, or omelet
# ForAll([p:people], Or(eats(p, snack) == fish, eats(p, snack) == omelet)) ::: For a snack, each eats exactly one of the following: fish or omelet
# eats(Wendy, lunch) == omelet ::: Wendy eats an omelet for lunch

# # Options
# Question ::: Vladimir must eat which one of the following foods?
# is_valid(Exists([m:meals], eats(Vladimir, m) == fish)) ::: (A)
# is_valid(Exists([m:meals], eats(Vladimir, m) == hot_cakes)) ::: (B)
# is_valid(Exists([m:meals], eats(Vladimir, m) == macaroni)) ::: (C)
# is_valid(Exists([m:meals], eats(Vladimir, m) == omelet)) ::: (D)
# is_valid(Exists([m:meals], eats(Vladimir, m) == poached_eggs)) ::: (E)'''

#     z3_program = LSAT_Z3_Program(logic_program, 'AR-LSAT')
#     print(z3_program.standard_code)

#     output, error_message = z3_program.execute_program()
#     print("Output:", output)
#     print("Error:", error_message)
    
#     if output is not None and len(output) > 0:
#         print("Answer:", z3_program.answer_mapping(output))
#     else:
#         print("No valid answer found or execution failed")