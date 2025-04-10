import os
import numpy as np
import json

from utils import processgenslots, preparegenslots, checktimecloseness


def _save_episode_dialogue(generated_dialogue, episode_path):
    with open(os.path.join(episode_path, "dialogue.json"), "w", encoding="utf-8") as f:
        json.dump(generated_dialogue, f, ensure_ascii=False, indent=4)

def getslotvaluesbycategories(slots: dict):
        infoslots = {}
        attrslots = {}
        bookslots = {}
        info_fail_slots = {}
        book_fail_slots = {}

        for domain, dvalue in slots.items():
            for key, kvalue in dvalue.items():
                if key == "info":
                    if domain not in infoslots:
                        infoslots[domain] = {}

                    for k, v in kvalue.items():
                        infoslots[domain][k] = v

                if key == "fail_info":
                    if domain not in info_fail_slots:
                        info_fail_slots[domain] = {}

                    for k, v in kvalue.items():
                        info_fail_slots[domain][k] = v                        

                elif key == "book":
                    if domain not in bookslots:
                        bookslots[domain] = {}

                    for k, v in kvalue.items():
                        if k in ["invalid", "pre_invalid"]:
                            continue
                        bookslots[domain][f"book{k}"] = v

                elif key == "fail_book":
                    if domain not in book_fail_slots:
                        book_fail_slots[domain] = {}

                    for k, v in kvalue.items():
                        if k in ["invalid", "pre_invalid"]:
                            continue
                        book_fail_slots[domain][f"book{k}"] = v                        

                elif key == "reqt":
                    if domain not in attrslots:
                        attrslots[domain] = {}
                    
                    attrslots[domain] = kvalue
                else:
                    continue

        return infoslots, bookslots, attrslots, info_fail_slots, book_fail_slots

def _setto_lower(slots: dict) -> dict:
    slots_conv = {}
    for domain, dvalue in slots.items():
        if isinstance(dvalue, dict):
            for key, value in dvalue.items():
                if domain.lower() not in slots_conv :
                    slots_conv[domain.lower()] = {}
                if isinstance(value, dict) or isinstance(value, list):
                    print(f"Value is a dict or list {value}")
                    input()
                slots_conv[domain.lower()][key.lower()] = str(value).lower()
        elif isinstance(dvalue, list):
            if domain.lower() not in slots_conv :
                slots_conv[domain.lower()] = {}
            
            slots_conv[domain.lower()] = [str(val).lower() for val in dvalue]
        else:
            print(f"Value is a scalar {dvalue}")
            input()
    return slots_conv



    #return {
    #        str(domain).lower(): {str(key).lower(): str(value).lower() for key, value in dvalue.items()}
    #        for domain, dvalue in slots.items()
    #    }


def _compare_slots(gt_slots: dict, gt_fail_slots: dict, gen_slots: dict):

    if not gt_slots:
        return False, "Ground truth slots are empty"
    
    if not gen_slots:
        return False, "Generated slots are empty"

    gtcompslots = _setto_lower(gt_slots)
    gtfailcompslots = _setto_lower(gt_fail_slots)
    gencompslots = _setto_lower(gen_slots)



    missed_domains = [domain for domain in gtcompslots if domain not in gencompslots]
    if missed_domains:
        #print(f"Domains of the ground truth slots and generated do not match {missed_domains}")
        return False, missed_domains

    missed_values = []
    for domain, dvalue in gtcompslots.items():
        missed_keys = [key for key in dvalue if key not in gencompslots[domain]]
        if missed_keys:
            #print(f"Keys of the ground truth slots and generated slots do not match {missed_keys}")
            return False, [{domain:missed_keys}]
        try:
            mvalues = []
            for key, value in dvalue.items():
                if value != gencompslots[domain][key]:
                    if domain in gtfailcompslots and key in gtfailcompslots[domain]:
                        if gtfailcompslots[domain][key] != gencompslots[domain][key]:
                            data_match = False
                            if key in ["leaveat", "arriveby"]:
                                data_match = True#checktimecloseness(gtfailcompslots[domain][key], gencompslots[domain][key])

                            if not data_match:
                                mvalues.append({domain: {"gt": {key: gtfailcompslots[domain][key]}, "gen": {key: gencompslots[domain][key]}}})
                        else:
                            #print(f"Key {key} has the same value {gencompslots[domain][key]} in the ground truth fail data and generated slots")
                            pass
                    else:
                        data_match = False
                        if key in ["leaveat", "arriveby"]:
                            data_match = True#checktimecloseness(value, gencompslots[domain][key])
                        
                        if not data_match:
                            mvalues.append({domain: {"gt": {key: value}, "gen": {key: gencompslots[domain][key]}}})
            if mvalues:
                missed_values.append({domain: mvalues})
        except Exception as error:
            print(f"Error in comparing values {error}")
            print(gtcompslots)
            print(gtfailcompslots)
            print(gencompslots)
            input()

    if missed_values:
        #print(f"Values of the ground truth slots and generated slots do not match {missed_values}")
        return False, missed_values                      
    
    return True, None


def compute_scores(base_dir):
    results = {}

    for model in os.listdir(base_dir):
        #Check if model is a directory
        if not os.path.isdir(os.path.join(base_dir, model)):
            continue
        #if "70B" not in model:
        #    continue
        model_path = os.path.join(base_dir, model)
        for game in os.listdir(model_path):
            if game not in results:
                results[game] = {}
            if model not in results[game]:
                results[game][model] = {}
            game_path = os.path.join(model_path, game)
            for exp in os.listdir(game_path):
                #if "xu" not in exp:
                #    continue
                if exp not in results[game][model]:
                    results[game][model][exp] = {}
                exp_path = os.path.join(game_path, exp)

                if not os.path.isdir(exp_path):
                    continue

                num_episodes = 0
                inform_ep_list = []
                book_ep_list = []
                attr_ep_list = []
                game_abort_list = []
                game_loss_list = []
                inform_ep_count = 0
                book_ep_count = 0
                attr_ep_count = 0
                game_abort_count = 0
                game_loss_count = 0

                for episode in os.listdir(exp_path):
                    episode_path = os.path.join(exp_path, episode)
                    if not os.path.isdir(episode_path):
                        continue

                    num_episodes += 1
                    for filename in os.listdir(episode_path):
                        if not filename in ["interactions.json"]:
                            continue

                        with open(os.path.join(episode_path, filename), "r") as f:
                            interaction_data = json.load(f)

                        _save_episode_dialogue(interaction_data["Evaluation"]["gendialogue"], episode_path)

                        game_abort = interaction_data["Aborted"]
                        game_loss = interaction_data["Lose"]

                        game_evaldata = interaction_data["Evaluation"]

                        dialogue_type = game_evaldata["dialogue_type"]
                        domains = game_evaldata["domains"]
                        tsystem = game_evaldata["tsystem"]
                        play_turns = game_evaldata["play_turns"]
                        n_turns = game_evaldata["n_turns"]
                        corpususer = game_evaldata["corpususer"]
                        gt_slots = game_evaldata["slots_gt"]
                        gen_slots = game_evaldata["slots_gen"]


                        if gen_slots:
                            if "xu" in exp or "he" in exp:
                                gen_slots_processed = preparegenslots(gen_slots)
                            else:
                                gen_slots_processed = processgenslots(gen_slots)
                        else:
                            gen_slots_processed = {}

                        if "slots_gen_loss" in game_evaldata:
                            gen_slots_loss = game_evaldata["slots_gen_loss"]
                        else:
                            gen_slots_loss = {}

                        data_to_save = {"play_turns": play_turns,
                                        "n_turns": n_turns,
                                        "dialogue_type": dialogue_type,
                                        "domains": domains,
                                        }
                        
                        if game_abort or play_turns == n_turns or gen_slots_processed is None:
                            inform_episode = 0
                            book_episode = 0
                            attr_episode = 0
                            if game_abort:
                                game_abort = 1

                        else:
                            game_abort = 0
                            infoslots_gt, bookslots_gt, attrslots_gt, infofailslots_gt, bookfailslots_gt = getslotvaluesbycategories(gt_slots)
                            infoslots_gen, bookslots_gen, attrslots_gen, *_ = getslotvaluesbycategories(gen_slots_processed)

                            status, _ = _compare_slots(infoslots_gt, infofailslots_gt, infoslots_gen)
                            if status:
                                inform_episode = 1
                                if not bookslots_gt:
                                    book_episode = 1
                                else:
                                    status, _ = _compare_slots(bookslots_gt, bookfailslots_gt, bookslots_gen)
                                    if status:
                                        book_episode = 1
                                    else:
                                        book_episode = 0
                                        game_loss = 1
                            else:
                                inform_episode = 0
                                book_episode = 0
                                game_loss = 1

                            if attrslots_gt:
                                status, _ = _compare_slots(attrslots_gt, attrslots_gen)
                                if status:
                                    attr_episode = 1
                                else:
                                    attr_episode = 0
                            else:
                                attr_episode = 1


                        inform_ep_list.append(inform_episode)
                        book_ep_list.append(book_episode)
                        attr_ep_list.append(attr_episode)
                        game_abort_list.append(game_abort)
                        game_loss_list.append(game_loss)
                        game_abort_count = len([1 for val in game_abort_list if val == 1])
                        game_loss_count = len([1 for val in game_loss_list if val == 1])
                        inform_ep_count = len([1 for val in inform_ep_list if val == 1])
                        book_ep_count = len([1 for val in book_ep_list if val == 1])
                        attr_ep_count = len([1 for val in attr_ep_list if val == 1])

                        break
                results[game][model][exp]["num_episodes"] = num_episodes
                results[game][model][exp]["entity_ext"] = round(np.mean(inform_ep_list), 2) if inform_ep_list else 0
                results[game][model][exp]["tasksuccess"] = round(np.mean(book_ep_list), 2) if book_ep_list else 0
                results[game][model][exp]["attr"] = round(np.mean(attr_ep_list), 2) if attr_ep_list else 0
                results[game][model][exp]["game_abort"] = round(np.mean(game_abort_list), 2) if game_abort_list else 0
                results[game][model][exp]["game_loss"] = round(np.mean(game_loss_list), 2) if game_loss_list else 0
                results[game][model][exp]["game_abort_count"] = game_abort_count
                results[game][model][exp]["game_loss_count"] = game_loss_count
                results[game][model][exp]["inform_ep_count"] = inform_ep_count
                results[game][model][exp]["book_ep_count"] = book_ep_count
                results[game][model][exp]["attr_ep_count"] = attr_ep_count

            #Compute the overall entity and task success results for the model
            results[game][model]["overall"] = {}
            overall_entity = []
            overall_tasksuccess = []
            overall_attr = []
            overall_game_abort = []
            overall_game_loss = []


            for exp in results[game][model]:
                if exp == "overall":
                    continue
                overall_entity.append(results[game][model][exp]["entity_ext"])
                overall_tasksuccess.append(results[game][model][exp]["tasksuccess"])
                overall_attr.append(results[game][model][exp]["attr"])
                overall_game_abort.append(results[game][model][exp]["game_abort"])
                overall_game_loss.append(results[game][model][exp]["game_loss"])


            for metric, value in zip(["entity_ext", "tasksuccess", "attr", "game_abort", "game_loss"], [overall_entity, overall_tasksuccess, overall_attr, overall_game_abort, overall_game_loss]):
                sdata = {"num_systems": (len(results[game][model])-1), "values": round(np.mean(value), 2) if value else 0}
                results[game][model]["overall"][metric] = sdata

    with open(os.path.join(base_dir, "taskmetrics.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("Task metrics computed and saved to taskmetrics.json")


compute_scores(
    "/home/admin/Desktop/codebase/cocobots/todsystems/clembench/modprog_single_2/"
)




