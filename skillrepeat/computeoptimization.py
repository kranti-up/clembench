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



class ASTComputation:
    def __init__(self):
        self.pcc = PutCallCounter()


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

    def get_calls_inside_loops(self, code: str) -> list:
        tree = ast.parse(code)
        results = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        # Extract the function name
                        if isinstance(child.func, ast.Name):
                            func_name = child.func.id          # simple call: foo()
                        elif isinstance(child.func, ast.Attribute):
                            func_name = child.func.attr        # method call: obj.foo()
                        else:
                            func_name = "unknown"

                        results.append({
                            "function": func_name,
                            "line": child.lineno,
                            "inside_loop_at_line": node.lineno
                        })

        return results        


    def islooppresent(self, generated_code):
        tree = ast.parse(generated_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                return int(True)
        return int(False)

    def hasputcalls(self, generated_code):
        try:
            output_tree = ast.parse(generated_code)
        except SyntaxError:
            return False  # generated code isn't even valid Python

        generated_puts = self.astcomp.count_put_calls(output_tree)

        if generated_puts:
            has_put_calls = True
        else:
            has_put_calls = False

        return int(has_put_calls)

    def getskillturnnumber(self, gencode, skillname):
        if not gencode:
            print("No gencode data to find skill turn number")
            input()

        turnnumbers = list(gencode.keys())
        if not turnnumbers:
            print("No turn numbers in gencode data")
            input()

        sortedturnnumbers = sorted(turnnumbers)
        for turnnum in sortedturnnumbers:
            if "clear" in gencode[turnnum] or "removeshape" in gencode[turnnum] or "move" in gencode[turnnum]:
                continue
            if skillname not in gencode[turnnum]:
                #print(f"Skill {skillname} not found in turn {turnnum} gencode: {gencode[turnnum]}")
                return False, False, False
        return True, False, False
            
  

    def parse_interactions(self, interactions: Dict[str, Any]):

        ev = interactions.get("Evaluation", None)
        if ev is None:
            print(f"Evaluation is None, cannot parse interactions")
            return None
        
        total_shapes = len(ev["boardinfo"]["regular"]["shapes"])
        comboname = ev["boardinfo"]["regular"]["combo_name"]

        repeat_genresponse = ev["genresponse"]["repeat"]
        if repeat_genresponse is None:
            print(f"optim_genresponse is None")
            return None
        
        repeat_gencode = {}
        for index, turn in enumerate(repeat_genresponse):
            if "response" not in turn:
                print(f"response is not available': {turn}")
                continue
            if turn["response"]["status"] == "code":
                repeat_gencode[index+1] = turn["response"]["details"]

        used_skill_1stturn, used_skill_lastturn, used_skill_anyturn = self.getskillturnnumber(repeat_gencode, comboname)                

        repeat_gencode_str = "\n".join(repeat_gencode.values())
        hasloop = self.islooppresent(repeat_gencode_str)
        used_with_putcalls = 0
        used_with_skill = 0
        if hasloop:
            calls_inside_loops = self.get_calls_inside_loops(repeat_gencode_str)
            if calls_inside_loops:
                calls_inside_loops_names = list(set(calls_inside_loops[i]["function"] for i in range(len(calls_inside_loops))))
                if "put" in calls_inside_loops_names:
                    used_with_putcalls = True
                    used_with_skill = False
                else:
                    used_with_putcalls = False
                    used_with_skill = True
                

        results = {"hasloop": hasloop, "used_with_putcalls": used_with_putcalls, "used_with_skill": used_with_skill, "total_shapes": total_shapes}
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

                    funcloop_ep: List[int] = []
                    total_func_loop = 0
                    epnums_with_loops = []
                    shape_stats = {}

                    for episode in tqdm(episodes, desc=f"{game}/{model}/{exp}"):
                        episode_path = os.path.join(exp_path, episode)
                        ep_stats, score_status = self.process_episode(episode_path)
                        if ep_stats is None:
                            #The episode might not be success, so the data is not computed
                            if score_status:
                                num_success_episodes += 1
                            continue
                        num_success_episodes += 1
                        funcloop_ep.append(ep_stats["hasloop"])

                        if ep_stats["hasloop"]:
                            epnums_with_loops.append(episode)
                        if ep_stats["total_shapes"] not in shape_stats:
                            shape_stats[ep_stats["total_shapes"]] = {"with_loops": 0, "total": 0, "ep_with_loops": [],  "used_loop_putcalls":0, "used_loop_skill": 0}
                        shape_stats[ep_stats["total_shapes"]]["total"] += 1
                        if ep_stats["hasloop"]:
                            shape_stats[ep_stats["total_shapes"]]["with_loops"] += 1
                            shape_stats[ep_stats["total_shapes"]]["ep_with_loops"].append(episode)
                            shape_stats[ep_stats["total_shapes"]]["used_loop_putcalls"] += int(ep_stats["used_with_putcalls"])
                            shape_stats[ep_stats["total_shapes"]]["used_loop_skill"] += int(ep_stats["used_with_skill"])



                    total_func_loop = sum(funcloop_ep)
                    func_loop_rate = round((total_func_loop/num_success_episodes), 2)

                    print(f"Number of Episodes: {num_episodes}, Success: {num_success_episodes}")
                    results[game][model][exp] = {"func_loop_rate": func_loop_rate, "totalepswithloops": total_func_loop,
                    "shape_stats": shape_stats}
                    #"epnums_with_loops": epnums_with_loops, "epnums_with_putcalls": epnums_with_putcalls}

        with open(f"{base_dir}/overall_optimal_results.json", "w") as f:
            json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?", default="rp_clpskills_gpt_4", help="Base directory containing model results")
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
