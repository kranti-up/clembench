import os
import numpy as np
import timeit
from typing import Dict, Any, List, Optional, Tuple
import json
import ast
import dis
import argparse
import types
from tqdm import tqdm


class PutCallCounter(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def visit_Call(self, node: ast.Call):
        # Matches `put(...)` (not obj.put or module.put)
        if isinstance(node.func, ast.Name) and node.func.id == "put":
            self.count += 1
        self.generic_visit(node)

class RemoveCallCounter(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def visit_Call(self, node: ast.Call):
        # Matches `removeshape(...)` (not obj.removeshape or module.removeshape)
        if isinstance(node.func, ast.Name) and node.func.id == "removeshape":
            self.count += 1
        self.generic_visit(node)

class MoveCallCounter(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def visit_Call(self, node: ast.Call):
        # Matches `move(...)` (not obj.move or module.move)
        if isinstance(node.func, ast.Name) and node.func.id == "move":
            self.count += 1
        self.generic_visit(node)

class ClearCallCounter(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def visit_Call(self, node: ast.Call):
        # Matches `clear(...)` (not obj.clear or module.clear)
        if isinstance(node.func, ast.Name) and node.func.id == "clear":
            self.count += 1
        self.generic_visit(node)        



class ASTComputation:
    def __init__(self):
        self.pcc = PutCallCounter()
        self.rcc = RemoveCallCounter()
        self.mcc = MoveCallCounter()
        self.ccc = ClearCallCounter()


    def get_top_level_function(self, tree: ast.AST):
        funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        return funcs[0] if funcs else None    
    
    def contains_function(self, code: str) -> bool:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False
        return self.get_top_level_function(tree) is not None    
    

    def count_put_calls(self, tree: ast.AST) -> int:
        self.pcc.count = 0
        self.pcc.visit(tree)
        return self.pcc.count  

    def count_remove_calls(self, tree: ast.AST) -> int:
        self.rcc.count = 0
        self.rcc.visit(tree)
        return self.rcc.count

    def count_move_calls(self, tree: ast.AST) -> int:
        self.mcc.count = 0
        self.mcc.visit(tree)
        return self.mcc.count

    def count_clear_calls(self, tree: ast.AST) -> int:
        self.ccc.count = 0
        self.ccc.visit(tree)
        return self.ccc.count

    def function_has_loop(self, func: ast.FunctionDef) -> bool:
        return any(isinstance(node, ast.For) for node in ast.walk(func))



class ComputeOptimalness:
    def __init__(self):
        self.astcomp = ASTComputation()


    def read_json_file(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return None        

    def isfuncnamelooppresent(self, generated_code):
        try:
            output_tree = ast.parse(generated_code)
        except SyntaxError:
            return False, None  # generated code isn't even valid Python


        func = self.astcomp.get_top_level_function(output_tree)
        if func is None:
            hasfuncname = False
        else:
            hasfuncname = True

        # Check it has a loop
        if not self.astcomp.function_has_loop(func):
            #return False, details
            hasloop = False
        else:
            hasloop = True
        return hasfuncname, hasloop

    def bytecode_len(self, fn):
        return len(list(dis.Bytecode(fn)))

    def bytecode_len_script(self, src: str) -> int:
        code = compile(src, "<string>", "exec")
        return len(code.co_code)    

    def bytecode_len_script_as_function(self, src: str) -> int:
        # Wrap the flat script in a dummy function
        wrapped = "def input_function():\n"
        for line in src.strip().split("\n"):
            wrapped += "    " + line + "\n"
        module_code = compile(wrapped, "<string>", "exec")
        for const in module_code.co_consts:
            if isinstance(const, types.CodeType):
                return len(const.co_code)
        raise ValueError("No function found")


    def bytecode_len_function(self, src: str) -> int:
        module_code = compile(src, "<string>", "exec")

        for const in module_code.co_consts:
            if isinstance(const, types.CodeType):
                return len(const.co_code)

        raise ValueError("No function found")            

    def isbytelenimproved(self, inputcode, generated_code):
        input_code_len = self.bytecode_len_script_as_function(inputcode)#self.bytecode_len_script(inputcode)
        generated_code_len = self.bytecode_len_function(generated_code)

        if generated_code_len < input_code_len:
            bytecode_len_reduction = True
        else:
            bytecode_len_reduction = False

        return bytecode_len_reduction, input_code_len, generated_code_len

    def numputcallsreduced(self, input_code, generated_code):
        try:
            input_tree = ast.parse(input_code)
            output_tree = ast.parse(generated_code)
        except SyntaxError:
            return False, None, None  # generated code isn't even valid Python

        input_puts = self.astcomp.count_put_calls(input_tree)
        generated_puts = self.astcomp.count_put_calls(output_tree)

        if not (1 <= generated_puts < input_puts):
            reduced_put_calls = False
        else:
            reduced_put_calls = True

        return reduced_put_calls, input_puts, generated_puts

    def numremovecallsreduced(self, input_code, generated_code):
        try:
            input_tree = ast.parse(input_code)
            output_tree = ast.parse(generated_code)
        except SyntaxError:
            return False, None, None  # generated code isn't even valid Python

        input_removes = self.astcomp.count_remove_calls(input_tree)
        generated_removes = self.astcomp.count_remove_calls(output_tree)

        if input_removes:
            print(f"Input removes: {input_removes}, generated removes: {generated_removes}")

        if input_removes:
            if generated_removes < input_removes:
                reduced_remove_calls = True
            else:
                reduced_remove_calls = False
        else:
            reduced_remove_calls = None


        return reduced_remove_calls, input_removes, generated_removes
    
    def nummovecallsreduced(self, input_code, generated_code):
        try:
            input_tree = ast.parse(input_code)
            output_tree = ast.parse(generated_code)
        except SyntaxError:
            return False, None, None  # generated code isn't even valid Python

        input_moves = self.astcomp.count_move_calls(input_tree)
        generated_moves = self.astcomp.count_move_calls(output_tree)

        if not (1 <= generated_moves < input_moves):
            reduced_move_calls = False
        else:
            reduced_move_calls = True

        return reduced_move_calls, input_moves, generated_moves

    def numclearcallsreduced(self, input_code, generated_code):
        try:
            input_tree = ast.parse(input_code)
            output_tree = ast.parse(generated_code)
        except SyntaxError:
            return False, None, None  # generated code isn't even valid Python

        input_clears = self.astcomp.count_clear_calls(input_tree)
        generated_clears = self.astcomp.count_clear_calls(output_tree)

        if not (1 <= generated_clears < input_clears):
            reduced_clear_calls = False
        else:
            reduced_clear_calls = True

        return reduced_clear_calls, input_clears, generated_clears    

    def parse_interactions(self, interactions: Dict[str, Any]):
        ev = interactions.get("Evaluation", None)
        if ev is None:
            print(f"Evaluation is None, cannot parse interactions")
            return None

        optimized_function = ev.get("optimized_function", None)
        if optimized_function is None:
            print(f"optimized_function is None")
            return None

        optim_genresponse = ev.get("optim_genresponse", None)
        if optim_genresponse is None:
            print(f"optim_genresponse is None")
            return None
        inst_code_pairs = optim_genresponse.get("inst_code_pairs", None)
        if inst_code_pairs is None:
            print(f"inst_code_pairs is None, {optim_genresponse}")
            return None
        
        input_code = ""
        for inst_code in inst_code_pairs:
            if inst_code["status"] == "code":
                input_code += inst_code["details"] + "\n"

        if not input_code:
            print(f"Input code is None, returning.. InstCodePairs: {inst_code_pairs}")
            return None

        hasfuncname, hasloop = self.isfuncnamelooppresent(optimized_function)
        reduced_put_calls, input_put, generated_put = self.numputcallsreduced(input_code, optimized_function)
        reduced_remove_calls, input_remove, generated_remove = self.numremovecallsreduced(input_code, optimized_function)
        reduced_move_calls, input_move, generated_move = self.nummovecallsreduced(input_code, optimized_function)
        reduced_clear_calls, input_clear, generated_clear = self.numclearcallsreduced(input_code, optimized_function)
        reduced_byte_len, input_bytelen, generated_bytelen = self.isbytelenimproved(input_code, optimized_function)

        results = {"hasfuncname": hasfuncname, "hasloop": hasloop, "reduced_put_calls": reduced_put_calls,
                   "reduced_byte_len": reduced_byte_len, "input_put": input_put, "generated_put": generated_put,
                    "reduced_remove_calls": reduced_remove_calls, "input_remove": input_remove, "generated_remove": generated_remove,
                    "reduced_move_calls": reduced_move_calls, "input_move": input_move, "generated_move": generated_move,
                    "reduced_clear_calls": reduced_clear_calls, "input_clear": input_clear, "generated_clear": generated_clear,
                   "input_bytelen": input_bytelen, "generated_bytelen": generated_bytelen, "input_code": input_code, "optimized_function": optimized_function }
        return results


    def process_episode(self, episode_path: str) -> Dict[str, Any]:

        interactions_path = os.path.join(episode_path, "interactions.json")

        if os.path.exists(interactions_path):
            interactions = self.read_json_file(interactions_path) or {}
        else:
            print(f"There is no interactions file in this path: {interactions_path}")
            return None, False

        if interactions:
            if interactions.get("Success") != True:
                return None, False

            return self.parse_interactions(interactions), True
        return None, False

    def run(self, base_dir):
        results: Dict[str, Any] = {}

        for model in os.listdir(base_dir):
            model_path = os.path.join(base_dir, model)
            if not os.path.isdir(model_path):
                continue

            for game in os.listdir(model_path):
                game_path = os.path.join(model_path, game)
                if not os.path.isdir(game_path):
                    continue
                results.setdefault(game, {})
                results[game].setdefault(model, {})

                for exp in os.listdir(game_path):
                    exp_path = os.path.join(game_path, exp)
                    if not os.path.isdir(exp_path):
                        continue

                    results[game][model].setdefault(exp, {})

                    episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                    num_episodes = len(episodes)
                    num_success_episodes = 0

                    funcname_ep: List[int] = []
                    funcloop_ep: List[int] = []
                    lessput_ep: List[int] = []
                    lessremove_ep: List[int] = []
                    lessmove_ep: List[int] = []
                    lessclear_ep: List[int] = []
                    lessbytelen_ep: List[int] = []
                    total_func_name = 0
                    total_func_loop = 0
                    total_less_putcalls = 0
                    total_less_remove_calls = 0
                    total_accurate_remove_calls = 0
                    total_less_move_calls = 0
                    total_less_clear_calls = 0
                    total_less_bytelen = 0

                    for episode in tqdm(episodes, desc=f"{game}/{model}/{exp}"):
                        episode_path = os.path.join(exp_path, episode)
                        ep_stats, score_status = self.process_episode(episode_path)
                        if ep_stats is None:
                            #The episode might not be success, so the data is not computed
                            if score_status:
                                num_success_episodes += 1
                            continue
                        num_success_episodes += 1
                        funcname_ep.append(ep_stats["hasfuncname"])
                        funcloop_ep.append(ep_stats["hasloop"])
                        lessput_ep.append({"status": ep_stats["reduced_put_calls"], "input_put": ep_stats["input_put"],
                         "generated_put": ep_stats["generated_put"]})
                        if ep_stats["reduced_remove_calls"] is not None:
                            lessremove_ep.append({"status": ep_stats["reduced_remove_calls"], "input_remove": ep_stats["input_remove"], "generated_remove": ep_stats["generated_remove"]})
                        lessmove_ep.append({"status": ep_stats["reduced_move_calls"], "input_move": ep_stats["input_move"],
                         "generated_move": ep_stats["generated_move"]})
                        lessclear_ep.append({"status": ep_stats["reduced_clear_calls"], "input_clear": ep_stats["input_clear"],
                         "generated_clear": ep_stats["generated_clear"]})
                        lessbytelen_ep.append({"status": ep_stats["reduced_byte_len"], "input_bytelen": ep_stats["input_bytelen"],
                         "generated_bytelen": ep_stats["generated_bytelen"], "input_code": ep_stats["input_code"], "optimized_function": ep_stats["optimized_function"]})
                        total_func_name += int(ep_stats["hasfuncname"])
                        total_func_loop += int(ep_stats["hasloop"])
                        total_less_putcalls += int(ep_stats["reduced_put_calls"])
                        if ep_stats["reduced_remove_calls"] is not None:
                            total_less_remove_calls += int(ep_stats["reduced_remove_calls"])
                            if ep_stats["reduced_remove_calls"]:
                                total_accurate_remove_calls += 1
                        total_less_move_calls += int(ep_stats["reduced_move_calls"])
                        total_less_clear_calls += int(ep_stats["reduced_clear_calls"])
                        total_less_bytelen += int(ep_stats["reduced_byte_len"])


                    func_name_rate = round((total_func_name/num_success_episodes), 2)
                    func_loop_rate = round((total_func_loop/num_success_episodes), 2)
                    func_less_putcalls_rate = round((total_less_putcalls/num_success_episodes), 2)
                    func_less_remove_calls_rate = round((total_accurate_remove_calls/total_less_remove_calls), 2)
                    func_less_move_calls_rate = round((total_less_move_calls/num_success_episodes), 2)
                    func_less_clear_calls_rate = round((total_less_clear_calls/num_success_episodes), 2)
                    func_less_bytelen_rate = round((total_less_bytelen/num_success_episodes), 2)

                    print(f"Number of Episodes: {num_episodes}, Success: {num_success_episodes}")
                    print(f"Func Name Rate: {func_name_rate}, func loop rate: {func_loop_rate}, less putcalls: {func_less_putcalls_rate}, less bytelen: {func_less_bytelen_rate}")
                    print(f"Less remove calls rate: {func_less_remove_calls_rate}, less move calls rate: {func_less_move_calls_rate}, less clear calls rate: {func_less_clear_calls_rate}")
                    results[game][model][exp] = {"func name rate": func_name_rate, "func_loop_rate": func_loop_rate,
                    "func_less_putcalls_rate": func_less_putcalls_rate, "func_less_remove_calls_rate": func_less_remove_calls_rate, "func_less_move_calls_rate": func_less_move_calls_rate,  "func_less_clear_calls_rate": func_less_clear_calls_rate,
                      "func_less_bytelen_rate": func_less_bytelen_rate,
                    "lessput_ep": lessput_ep, "lessbytelen_ep": lessbytelen_ep, "lessremove_ep": lessremove_ep, "lessmove_ep": lessmove_ep, "lessclear_ep": lessclear_ep}

        with open(f"{base_dir}/overall_optimal_results.json", "w") as f:
            json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?", default="rskills_clp_2", help="Base directory containing model results")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose printing")
    args = parser.parse_args()

    cscores = ComputeOptimalness()
    cscores.run(args.base_dir)

    """
    test_code1 = "put(board, 'washer', 'red', 3, 2)\nput(board, 'nut', 'blue', 3, 3)\nput(board, 'bridge-h', 'green', 3, 2)\nput(board, 'screw', 'red', 3, 2)\n"
    print(cscores.bytecode_len_script(test_code1))

    test_code2 = "def wnbhs(board, colors, x, y):\n    # Define the shapes and their relative positions\n    shapes = ['washer', 'nut', 'bridge-h', 'screw']\n    relative_positions = [(0, 0), (0, 1), (0, 0), (0, 0)]\n    \n    # Colors list: red, blue, green, red\n    # Place each shape with its corresponding color and relative offset\n    for i, (shape, (dx, dy)) in enumerate(zip(shapes, relative_positions)):\n        put(board, shape, colors[i], x + dx, y + dy)"
    print(cscores.bytecode_len_function(test_code2))

    code1 = compile(test_code1, "<string>", "exec")
    code2 = compile(test_code2, "<string>", "exec")    

    instructions1 = list(dis.get_instructions(code1))
    instructions2 = list(dis.get_instructions(code2))

    print(f"Code1 instruction count: {len(instructions1)}")
    print(f"Code2 instruction count: {len(instructions2)}")

    # Byte length of raw bytecode
    print(f"Code1 bytecode bytes: {len(code1.co_code)}")
    print(f"Code2 bytecode bytes: {len(code2.co_code)}")

    inner_code2 = code2.co_consts[0]  # the 'wn' function code object

    print(f"Code1 bytecode bytes: {len(code1.co_code)}")
    print(f"Code2 (inner fn) bytecode bytes: {len(inner_code2.co_code)}")
    """
    # To see the full disassembly:
    #print("\n--- Code1 ---")
    #dis.dis(code1)

    #print("\n--- Code2 (inner fn) ---")
    #dis.dis(inner_code2)    


if __name__ == "__main__":
    main()    
