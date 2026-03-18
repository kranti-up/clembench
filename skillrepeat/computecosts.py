import os
import json
from typing import Dict, Any, List, Optional, Tuple


class ComputeAPICosts:
    def __init__(self):
        pass

    def readfile(self, filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    
    def getcost(self, model: str) -> Optional[float]:
        model_costs = {
            "openai/gpt-5.2-codex": {"input_tokens": 1.75, "output_tokens": 14},  # $1.75 per 1M input tokens, $14 per 1M output tokens
            "anthropic/claude-sonnet-4.5": {"input_tokens": 3, "output_tokens": 15},  # $3 per 1M input tokens, $15 per 1M output tokens
            "qwen3-coder-30B": {"input_tokens": 0.07, "output_tokens": 0.27},  # $0.02 per 1K input tokens, $0.04 per 1K output tokens
            "clp-chat-2-t0.0": {"input_tokens": 0.07, "output_tokens": 0.27},  # $0.07 per 1M input tokens, $0.27 per 1M output tokens
            "upgpt-codex-t0.0": {"input_tokens": 1.75, "output_tokens": 14},  # $1.75 per 1M input tokens, $14 per 1M output tokens
            "human-t0.0": {"input_tokens": 0, "output_tokens": 0},  # $0.00 per 1M input tokens, $0 per 1M output tokens
        }
        return model_costs.get(model, None)

    def computecosts(self, model: str, input_tokens: int, output_tokens: int, compute_type: str) -> Optional[float]:
        if "--" in model:
            model_split = model.split("--")
            if len(model_split) > 1:
                usmodel = model_split[0]
                cobotmodel = model_split[1]
                if compute_type == "usersimulator":
                    use_model_name = usmodel
                elif compute_type == "cobot":
                    use_model_name = cobotmodel
                elif compute_type == "cobot-optimizer":
                    use_model_name = cobotmodel
                else:
                    print(f"Unknown compute type {compute_type} for model {model}")
                    input()
            else:
                print(f"Model name {model} is not in expected format with '--' ")
                input()
        else:
            use_model_name = model


        cost_per_token = self.getcost(use_model_name)
        if cost_per_token is None:
            print(f"Cost for model {use_model_name} not found.")
            return None

        total_cost = ((input_tokens/1000000) * cost_per_token["input_tokens"] + (output_tokens/1000000) * cost_per_token["output_tokens"])
        return total_cost
    
    def _parse_messagetext(self, response_obj, model_name):
        model_name = response_obj.get("model", model_name)  # Fallback to provided model_name if not in response_obj
        if "--" in model_name:
            print(f"Model name {model_name} contains '--' ")
            input()


        if model_name in ["qwen3-coder-30B", "clp-chat-2-t0.0", "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"]:
            messagelist = response_obj.get("choices", "")
            message = messagelist[0].get("message", None) if messagelist else None
            if message:
                content = message.get("content", "")
                if content.startswith("[[ ## instruction ## ]]"):
                    token_role = "usersimulator"
                elif content.startswith("[[ ## player_response ## ]]"):
                    token_role = "cobot"
                elif content.startswith("[[ ## optimized_function ## ]]"):
                    token_role = "cobot-optimizer"                    
                else:
                    #print(type(content))
                    #print(f"Content does not start with expected prefixes: {content} for model {model_name}")
                    #input()
                    if "status" in content:
                        token_role = "cobot"
                    else:
                        token_role = "usersimulator"
                    #token_role = "unknown"
            else:
                print(f"Message is None or empty in response object: {response_obj.get('choices', '')} for model {model_name}")
                token_role = "unknown"
        elif model_name in ["openai/gpt-5.2-codex", "upgpt-codex-t0.0", "gpt-5.2-codex"]:
            messagelist = response_obj.get("output", [])
            if messagelist:
                if len(messagelist) > 1:
                    content = messagelist[-1]["content"]
                else:
                    content = messagelist[0]["content"]
                
                if content is None:
                    print(f"Content is None in response object: {response_obj['output']}, {len(response_obj['output'])}")
                    input()
                    token_role = "unknown"
                else:
                    text = content[0]["text"]
                    if text.startswith("[[ ## instruction ## ]]") or text.startswith("[[ ## instruction ##"):
                        token_role = "usersimulator"
                    elif text.startswith("[[ ## player_response ## ]]") or text.startswith("[[ ## player_response ##"):
                        token_role = "cobot"
                    elif text.startswith("[[ ## optimized_function ## ]]") or text.startswith("[[ ## optimized_function ##"):
                        token_role = "cobot-optimizer"
                    else:
                        print(f"Text does not start with expected prefixes: {text} for model {model_name}")
                        input()
                        token_role = "unknown"


        return token_role

    def _process_human_episode(self, model_name, requestsdata, stats):
        reqcalls = requestsdata["calls"]

        for req in reqcalls:
            token_usage = req["call"]["raw_response_obj"].get("usage", {})
            if "prompt_tokens" in token_usage:
                use_input = "prompt_tokens"
            elif "input_tokens" in token_usage:
                use_input = "input_tokens"
            else:
                print(f"Suitable key for input tokens is not found {token_usage.keys()}")
                input()

            if "completion_tokens" in token_usage:
                use_output = "completion_tokens"
            elif "output_tokens" in token_usage:
                use_output = "output_tokens"
            else:
                print(f"Suitable key for output tokens is not found {token_usage.keys()}")
                input()

            input_tokens = token_usage.get(use_input, 0)
            output_tokens = token_usage.get(use_output, 0)
            total_tokens = token_usage.get("total_tokens", 0)

            token_role = self._parse_messagetext(req["call"]["raw_response_obj"], model_name)

            stats[token_role]["input_tokens"] += input_tokens
            stats[token_role]["output_tokens"] += output_tokens
            stats[token_role]["total_tokens"] += total_tokens
            stats[token_role]["num_calls"] += 1


    def process_episode(self, model_name, episode_path: str) -> Dict[str, Any]:
        if "human" in model_name.lower():
            usefilename = "player_2.requests.json"
        else:
            usefilename = "requests.json"
        requests_path = os.path.join(episode_path, usefilename)

        requestsdata = None
        stats = {"usersimulator": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                "cobot": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                "cobot-optimizer":{"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                "unknown": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0}
                }


        if os.path.exists(requests_path):
            #print(f"Processing requests data from {requests_path}...")
            requestsdata = self.readfile(requests_path)

        else:
            #print(f"Requests data not found at {requests_path}. Skipping episode.")
            #input()
            return stats


        if requestsdata is None:
            #raise ValueError(f"Failed to read requests data from {requests_path}.")
            print(f"Failed to read requests data from {requests_path}.")
            input()
            return stats

        if "human" in model_name.lower():
            self._process_human_episode(model_name, requestsdata, stats)
            return stats

        for req in requestsdata:
            if "raw_response_obj" not in req:
                continue
            token_usage = req["raw_response_obj"].get("usage", {})
            if "prompt_tokens" in token_usage:
                use_input = "prompt_tokens"
            elif "input_tokens" in token_usage:
                use_input = "input_tokens"
            else:
                print(f"Suitable key for input tokens is not found {token_usage.keys()}")
                input()

            if "completion_tokens" in token_usage:
                use_output = "completion_tokens"
            elif "output_tokens" in token_usage:
                use_output = "output_tokens"
            else:
                print(f"Suitable key for output tokens is not found {token_usage.keys()}")
                input()

            input_tokens = token_usage.get(use_input, 0)
            output_tokens = token_usage.get(use_output, 0)
            total_tokens = token_usage.get("total_tokens", 0)

            token_role = self._parse_messagetext(req["raw_response_obj"], model_name)

            stats[token_role]["input_tokens"] += input_tokens
            stats[token_role]["output_tokens"] += output_tokens
            stats[token_role]["total_tokens"] += total_tokens
            stats[token_role]["num_calls"] += 1

        return stats

    def getskillepnums(self, base_dir, modelname):
        filename = f"{base_dir}/{modelname}_skillrepeat_zs_skillavaileps.json"
        with open(filename, 'r') as file:
            data = json.load(file)
        return data

    def getnoskillepnums(self, base_dir, modelname, useclp=False):
        usemodel = "clp" if useclp else "gpt"
        filename = f"{base_dir}/{modelname}_skillrepeat_zs_noskill_eps_{usemodel}.json"
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"File not found: {filename}")
            data = []
        return data

    def run(self, base_dir):
        if not base_dir:
            raise ValueError("Basedir must be provided.")
        
        
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            raise ValueError(f"Basedir {base_dir} does not exist.")
        
        costinfo = {}

        for model in os.listdir(base_dir):
            model_path = os.path.join(base_dir, model)
            if not os.path.isdir(model_path):
                continue
            costinfo[model] = {}

            skillepnums = self.getskillepnums(base_dir, model)
            noskillepnums_clp = self.getnoskillepnums(base_dir, model, useclp=True)
            noskillepnums_gpt = self.getnoskillepnums(base_dir, model, useclp=False)


            for game in os.listdir(model_path):
                game_path = os.path.join(model_path, game)
                if not os.path.isdir(game_path):
                    continue

                costinfo[model][game] = {}

                for exp in os.listdir(game_path):
                    exp_path = os.path.join(game_path, exp)
                    if not os.path.isdir(exp_path):
                        continue

                    costinfo[model][game][exp] = {"overall": {}}#, "skills": {}, "no_skills": {}}

                    episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                    num_episodes = len(episodes)
                    token_stats = {"usersimulator": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot-optimizer":{"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "unknown": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0}
                                   }
                    token_stats_skills_avail = {"usersimulator": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot-optimizer":{"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "unknown": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0}
                                   }
                    token_stats_skills_notavail = {"usersimulator": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot-optimizer":{"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "unknown": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0}
                                   }                    

                    token_stats_noskills_clp = {"usersimulator": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot-optimizer":{"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "unknown": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0}
                                   }                    

                    token_stats_noskills_gpt = {"usersimulator": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "cobot-optimizer":{"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0},
                                   "unknown": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_calls": 0}
                                   }                    


                    for episode in episodes:
                        episode_path = os.path.join(exp_path, episode)
                        ep_stats = self.process_episode(model, episode_path)

                        for role, stats in ep_stats.items():
                            for key, value in stats.items():
                                token_stats[role][key] += value

                                if episode in skillepnums:
                                    token_stats_skills_avail[role][key] += value
                                else:
                                    token_stats_skills_notavail[role][key] += value

                                if episode in noskillepnums_clp:
                                    token_stats_noskills_clp[role][key] += value
                                if episode in noskillepnums_gpt:
                                    token_stats_noskills_gpt[role][key] += value

                    #print(f"Model: {model}, Game: {game}, Exp: {exp}, Num Episodes: {num_episodes}, Token Stats: {token_stats}")
                    use_model_name = model#"anthropic/claude-sonnet-4.5"#"openai/gpt-5.2-codex"#"anthropic/claude-sonnet-4.5"

                    for stats_type in ["overall", "skills_avail", "skills_notavail", "noskills_clp", "noskills_gpt"]:
                        if stats_type == "overall":
                            token_stats_to_use = token_stats
                        elif stats_type == "skills_avail":
                            token_stats_to_use = token_stats_skills_avail
                        elif stats_type == "skills_notavail":
                            token_stats_to_use = token_stats_skills_notavail
                        elif stats_type == "noskills_clp":
                            token_stats_to_use = token_stats_noskills_clp
                        elif stats_type == "noskills_gpt":
                            token_stats_to_use = token_stats_noskills_gpt
                        else:
                            print(f"Unknown stats type {stats_type}")
                            input()
                            continue

                        us_cost = self.computecosts(use_model_name, token_stats_to_use["usersimulator"]["input_tokens"], token_stats_to_use["usersimulator"]["output_tokens"], "usersimulator")
                        cobot_cost = self.computecosts(use_model_name, token_stats_to_use["cobot"]["input_tokens"], token_stats_to_use["cobot"]["output_tokens"], "cobot")
                        if "cobot-optimizer" in token_stats_to_use and (token_stats_to_use["cobot-optimizer"]["input_tokens"] > 0 or token_stats_to_use["cobot-optimizer"]["output_tokens"] > 0):
                            cobot_optim_cost = self.computecosts(use_model_name, token_stats_to_use["cobot-optimizer"]["input_tokens"], token_stats_to_use["cobot-optimizer"]["output_tokens"], "cobot-optimizer") 
                        else:
                            cobot_optim_cost = 0
                        if "unknown" in token_stats_to_use and (token_stats_to_use["unknown"]["input_tokens"] > 0 or token_stats_to_use["unknown"]["output_tokens"] > 0):
                            print(f"Computing cost for unknown tokens with token stats {token_stats_to_use['unknown']}")
                            unknown_cost = self.computecosts(use_model_name, token_stats_to_use["unknown"]["input_tokens"], token_stats_to_use["unknown"]["output_tokens"], "unknown")
                        else:
                            unknown_cost = 0
                        total_cost = sum(cost for cost in [us_cost, cobot_cost, cobot_optim_cost, unknown_cost] if cost is not None)
                        print(f"Model: {use_model_name}, Game: {game}, Exp: {exp}, StatsType: {stats_type}, \n Total Cost: ${total_cost:.2f} (User Simulator: ${us_cost:.2f}, CoBot: ${cobot_cost:.2f}, Cobot-Optimizer: ${cobot_optim_cost:.2f}, Unknown: ${unknown_cost:.2f})\n\n")
                        costinfo[model][game][exp][stats_type] = {"total_cost": round(total_cost, 2), "user_simulator_cost": round(us_cost, 2), "cobot_cost": round(cobot_cost, 2), "cobot_optim cost": round(cobot_optim_cost, 2), "unknown_cost": round(unknown_cost, 2), "token_stats": token_stats_to_use}

        with open(f"{base_dir}/costinfo.json", 'w', encoding='utf-8') as file:
            json.dump(costinfo, file, indent=4)

        

if __name__ == "__main__":
    base_dir = "rp_noskills_clp_gpt_4"
    compute_costs = ComputeAPICosts()
    compute_costs.run(base_dir)
