import os
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from utils.prepareasciirep import PrepareASCIIRep


def read_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def isinstanceinfoavailable(episode_path):
    interactions_path = os.path.join(episode_path, "interactions.json")
    if os.path.exists(interactions_path):
        return True
    return False

def _prepare_instance_info(episode_path):
    interaction_data = {}
    interactions_path = os.path.join(episode_path, "interactions.json")
    if os.path.exists(interactions_path):
        interactions = read_json_file(interactions_path) or {}
        if "Success" not in interactions:
            print(f"Episode {episode_path} interactions data is missing Success field")
            return None
        interaction_data["overall_success"] = interactions["Success"]
        interaction_data["overall_abort"] = interactions["Aborted"]
        interaction_data["overall_loss"] = interactions["Lose"]                

        ev = interactions.get("Evaluation", {})
        boardinfo = ev["boardinfo"]["regular"]
        interaction_data["shapes"] = boardinfo["shapes"]
        interaction_data["num_shapes"] = len(interaction_data["shapes"])
        interaction_data["comboname"] = boardinfo["combo_name"]
        interaction_data["colors"] = boardinfo["colors"]
        interaction_data["repeat_gt_code_board"] = {"function": boardinfo["code"]["function"],
                        "usage": boardinfo["code"]["output"],}
        #interaction_data["repeat_gt_code_validation"] = ev["used_gtcode_for_validation"]
        interaction_data["repeatinput_code"] = ev["repeat_input_data"]
        #interaction_data["reuseplay_turns"] = ev["play_turns"]
        interaction_data["repeatplay_turns"] = len(ev["genresponse"]["repeat"])

        if "skillandtargetcellsdiscrep" in ev:
            interaction_data["skillandtargetcellsdiscrep"] = ev["skillandtargetcellsdiscrep"]
        else:
            interaction_data["skillandtargetcellsdiscrep"] = False

        interaction_data["useskills"] = ev["use_skills"]
        interaction_data["skillsfilename"] = ev["existing_skills_filename"]
        interaction_data["skillscode"] = ev["skills_code"]
        interaction_data["use_oracle_code"] = ev["use_oracle_code"]
        interaction_data["used_oracle_code_as_skill_not_available"] = ev["used_oracle_code_as_skill_not_available"]
        interaction_data["repeat_success"] = ev["repeat_success"]
        interaction_data["genresponse"] = ev["genresponse"]
        interaction_data["turncode"] = interaction_data["genresponse"]["repeat"]
        interaction_data["geninstructions"] = {}
        interaction_data["gencode"] = {}
        interaction_data["gencfq"] = {}
        interaction_data["genothers"] = {}
        for index, turn in enumerate(interaction_data["turncode"]):
            if "instruction" not in turn:
                if interaction_data["overall_abort"]:
                    continue

                print(f"Episode {episode_path} is missing instructions in genresponse\n{turn}")
                input()
            interaction_data["geninstructions"][index+1] = turn["instruction"]

            if "response" not in turn:
                if interaction_data["overall_abort"]:
                    continue
                print(f"Episode {episode_path} is missing response in genresponse\n{turn}")
                input()

            resp_status = turn["response"]["status"]
            if resp_status == "code":
                interaction_data["gencode"][index+1] = turn["response"]["details"]
            elif resp_status == "clarification":
                interaction_data["gencfq"][index+1] = turn["response"]["details"]
            else:
                interaction_data["genothers"][index+1] = {turn["response"]["status"]: turn["response"]["details"]}

        interaction_data["repeat_response"] = ev.get("repeat_genresponse", {})
        repeat_response = interaction_data["repeat_response"] 
        interaction_data["used_clarification"] = repeat_response["used_clarification"]
        interaction_data["num_clarification"] = repeat_response["num_clarifications"]        
        interaction_data["used_remove"] = repeat_response["used_remove"]
        interaction_data["num_removes"] = repeat_response["num_removes"]
        interaction_data["used_move"] = repeat_response["used_move"]
        interaction_data["num_move"] = repeat_response["num_moves"]
        interaction_data["used_undo"] = repeat_response["used_undo"]
        interaction_data["num_undo"] = repeat_response["num_undos"]
        interaction_data["used_clear"] = repeat_response["used_clear"]
        interaction_data["num_clear"] = repeat_response["num_clears"]
        return interaction_data
    else:
        return None

def getskillturnnumber(gencode, skillname):
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
            


    if skillname in gencode[sortedturnnumbers[0]]:
        return True, False, False
    

    if skillname in gencode[sortedturnnumbers[-1]]:
        return False, True, False
    else:
        for turnnum in sortedturnnumbers[1:-1]:
            if skillname in gencode[turnnum]:
                return False, False, True
        return False, False, False


def process_episode(episode_path: str, statsdict, clpskills, gptskills) -> Dict[str, Any]:
    
    interavail = isinstanceinfoavailable(episode_path)
    if not interavail:
        return

    interdata = _prepare_instance_info(episode_path)
    if not interdata:
        return

    episode_num = episode_path.split("/")[-1]


    if interdata["overall_success"] != interdata["repeat_success"]:
        print(f"Difference between overall success and repeat success flag for episode: {episode_num}")
        input()

    play_turns = interdata["repeatplay_turns"]

    if len(interdata["gencode"]) > play_turns:
        print(f"Code Generation turns are more than play turns: {episode_num}")
        print(f'play_turns: {play_turns}, gencodelength: {len(interdata["gencode"])}')
        input()

    used_skill_1stturn, used_skill_lastturn, used_skill_anyturn = False, False, False

    if interdata["overall_loss"]:
        statsdict["faileps"].append({episode_num:play_turns})
        statsdict["shape_stats"][interdata["num_shapes"]]["faileps"] += 1

    elif interdata["overall_success"]:
        statsdict["successeps"].append({episode_num:play_turns})
        statsdict["shape_stats"][interdata["num_shapes"]]["successeps"] += 1
        used_skill_1stturn, used_skill_lastturn, used_skill_anyturn = getskillturnnumber(interdata["gencode"], interdata["comboname"])
        if used_skill_1stturn and used_skill_lastturn and used_skill_anyturn:
            print(f"Combo {interdata['comboname']} appears in both first and last turn and also in middle turns for episode {episode_num}")
            input()        

    elif interdata["overall_abort"]:
        statsdict["aborteps"].append({episode_num:play_turns})
        statsdict["shape_stats"][interdata["num_shapes"]]["aborteps"] += 1


    if interdata["gencfq"] and interdata["used_clarification"] == False:
        print(f"Difference between cfq flag and genresponse for episode: {episode_num}")
        input()

    if interdata["skillscode"] is None and interdata["useskills"]:
        print(f"Difference between skillcode data and useskills flag for episode: {episode_num}")
        input()

    if not interdata["useskills"]:
        #Skills are not used, however we need this to compute the instances improvement for using the skills
        #Check if this comboname is existing in clpskills, gptskills
        #If the skill exists add these eps to a new list and categorize success, abort and failure
        #While processing save these ep numbers to a file, so that we can compute the costs
        clpskillcombos = list(clpskills.keys())
        gptskillcombos = list(gptskills.keys())
        if interdata["comboname"] in clpskills:
            if interdata["overall_success"]:
                statsdict["noskills"]["clp"]["successeps"].append({episode_num:play_turns})
            elif interdata["overall_abort"]:
                statsdict["noskills"]["clp"]["aborteps"].append({episode_num:play_turns})
            elif interdata["overall_loss"]:
                statsdict["noskills"]["clp"]["faileps"].append({episode_num:play_turns})
        if interdata["comboname"] in gptskills:
            if interdata["overall_success"]:
                statsdict["noskills"]["gpt"]["successeps"].append({episode_num:play_turns})
            elif interdata["overall_abort"]:
                statsdict["noskills"]["gpt"]["aborteps"].append({episode_num:play_turns})
            elif interdata["overall_loss"]:
                statsdict["noskills"]["gpt"]["faileps"].append({episode_num:play_turns})


    code_stats = {"move": 0, "remove": 0, "clear": 0, "undo": 0}
    if interdata["gencode"]:
        for turnnum, codedata in interdata["gencode"].items():
            if codedata:
                # TODO:If a turn code contains multiple move() instances, it will still count as 1. We can change this to count the number of instances if needed.
                if "move(" in codedata:
                    code_stats["move"] += 1
                if "remove(" in codedata:
                    code_stats["remove"] += 1
                if "clear(" in codedata:
                    code_stats["clear"] += 1
                if "undo(" in codedata:
                    code_stats["undo"] += 1

    if interdata["used_clarification"]:
        statsdict["clarification_eps"].append({interdata["num_shapes"]:{interdata["comboname"]:{episode_num:play_turns, "success": interdata["overall_success"], "abort": interdata["overall_abort"]}}})

    if interdata["used_remove"] or interdata["used_move"] or interdata["used_clear"] or code_stats["move"] or code_stats["remove"] or code_stats["clear"]:
        statsdict["correction_eps"].append({interdata["num_shapes"]:{interdata["comboname"]:{episode_num:play_turns, "success": interdata["overall_success"], "abort": interdata["overall_abort"], "code_stats": code_stats}}})

    if interdata["used_undo"] or code_stats["undo"]:
        statsdict["undo_eps"].append({episode_num:play_turns})

    statsdict["num_turns"].append({episode_num:play_turns})

    if interdata["used_oracle_code_as_skill_not_available"]:
        statsdict["skill_unavail_eps"].append({interdata["num_shapes"]:{interdata["comboname"]:{episode_num:play_turns}}})

    if interdata["use_oracle_code"]:
        statsdict["skill_oracle_eps"].append({episode_num:play_turns})


    statsdict["gencode"].append({episode_num:interdata["gencode"]})
    statsdict["geninstructions"].append({episode_num:interdata["geninstructions"]})

    statsdict["num_turns_code_gen"].append({episode_num:{len(interdata["gencode"]): interdata["gencode"]}})
    statsdict["num_skills"] = len(interdata["skillscode"]) if interdata["skillscode"] else 0

    if interdata["skillsfilename"] not in statsdict["skillsfilename"]:
        statsdict["skillsfilename"][interdata["skillsfilename"]] = 0
    statsdict["skillsfilename"][interdata["skillsfilename"]] += 1

    if interdata["skillandtargetcellsdiscrep"]:
        if interdata["overall_success"]:
            statsdict["skillandtargetcellsdiscrep"]["success"].append({interdata["comboname"]:episode_num})
        elif interdata["overall_abort"]:
            statsdict["skillandtargetcellsdiscrep"]["abort"].append({interdata["comboname"]:episode_num})
        else:
            statsdict["skillandtargetcellsdiscrep"]["failure"].append({interdata["comboname"]:episode_num})

    if interdata["skillscode"]:
        if interdata["comboname"] not in interdata["skillscode"]:
            statsdict["skillnotavailcombos"].append(interdata["comboname"])
            statsdict["skillnotavailepscnt"]+=1
            if interdata["overall_success"]:
                statsdict["successepsfromscratch"].append({"episode_num": episode_num, "play_turns": play_turns, "num_shapes": interdata["num_shapes"], "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn,})
            elif interdata["overall_abort"]:
                statsdict["abortepsfromscratch"].append({"episode_num": episode_num, "play_turns": play_turns, "num_shapes": interdata["num_shapes"], "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn,})
            elif interdata["overall_loss"]:
                statsdict["failepsfromscratch"].append({"episode_num": episode_num, "play_turns": play_turns, "num_shapes": interdata["num_shapes"], "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn,})

        elif interdata["comboname"] in interdata["skillscode"]:
            statsdict["skillavailcombos"].append(interdata["comboname"])
            statsdict["skillavailepscnt"]+=1
            if interdata["overall_success"]:
                statsdict["successepsskill"].append({"episode_num": episode_num, "play_turns": play_turns, "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn, "num_shapes": interdata["num_shapes"]})
            elif interdata["overall_abort"]:
                statsdict["abortepsskill"].append({"episode_num": episode_num, "play_turns": play_turns, "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn, "num_shapes": interdata["num_shapes"]})
            elif interdata["overall_loss"]:
                statsdict["failepsskill"].append({"episode_num": episode_num, "play_turns": play_turns, "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn, "num_shapes": interdata["num_shapes"]})
    else:
        statsdict["skillnotavailcombos"].append(interdata["comboname"])
        statsdict["skillnotavailepscnt"]+=1
        if interdata["overall_success"]:
            statsdict["successepsfromscratch"].append({"episode_num": episode_num, "play_turns": play_turns, "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn, "num_shapes": interdata["num_shapes"]})
        elif interdata["overall_abort"]:
            statsdict["abortepsfromscratch"].append({"episode_num": episode_num, "play_turns": play_turns, "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn, "num_shapes": interdata["num_shapes"]})
        elif interdata["overall_loss"]:
            statsdict["failepsfromscratch"].append({"episode_num": episode_num, "play_turns": play_turns, "used_skill_1stturn": used_skill_1stturn, "used_skill_lastturn": used_skill_lastturn, "used_skill_anyturn": used_skill_anyturn, "num_shapes": interdata["num_shapes"]})


def _process_skill_discrepancy(expstats):
    if expstats is None:
        return

    skillandtargetcellsdiscrep = expstats["skillandtargetcellsdiscrep"]
    discrepancy_details = {}

    discrepancy_details["total_discrepancies"] = len(skillandtargetcellsdiscrep["success"]) + len(skillandtargetcellsdiscrep["abort"]) + len(skillandtargetcellsdiscrep["failure"])

    discrepancy_details["combos"] = {"success": [], "abort": [], "failure": []}
    for status in ["success", "abort", "failure"]:
        if skillandtargetcellsdiscrep[status]:
            discrepancy_details[f"{status}_eps"] = []
            for combo_eps in skillandtargetcellsdiscrep[status]:
                combo_name = list(combo_eps.keys())[0]
                episode_num = combo_eps[combo_name]
                #print(f"Combo: {combo_name}, Episode: {episode_num}, Discrepancy Type: {status}")
                discrepancy_details[f"{status}_eps"].append(episode_num)
                discrepancy_details["combos"][f"{status}"].append(combo_name)
    

    if discrepancy_details["total_discrepancies"]:
        discrepancy_details["success"] = round((len(skillandtargetcellsdiscrep["success"])/discrepancy_details["total_discrepancies"]),3)
        discrepancy_details["abort"] = round((len(skillandtargetcellsdiscrep["abort"])/discrepancy_details["total_discrepancies"]),3)
        discrepancy_details["failure"] = round((len(skillandtargetcellsdiscrep["failure"])/discrepancy_details["total_discrepancies"]),3)
    else:
        discrepancy_details["success"] = 0
        discrepancy_details["abort"] = 0
        discrepancy_details["failure"] = 0

    return discrepancy_details

def _process_correction_data(expstats):
    if expstats is None:
        return

    correpisodes = expstats["correction_eps"]
    num_success = 0
    num_abort = 0
    num_failure = 0
    corrdata = {}
    for data in correpisodes:
        shapeval = list(data.keys())[0]
        if shapeval not in corrdata:
            corrdata[shapeval] = {}
        combodata = data[shapeval]
        comboname = list(combodata.keys())[0]
        if comboname not in corrdata[shapeval]:
            corrdata[shapeval][comboname] = {}
        if combodata[comboname]["success"]:
            num_success+=1
        elif combodata[comboname]["abort"]:
            num_abort+=1
        else:
            num_failure+=1
        combodata[comboname].pop("success")
        combodata[comboname].pop("abort")
        corrdata[shapeval][comboname].update(combodata[comboname])  

    corr_counts_per_shape = {}
    corr_turns_per_shape = {}
    corr_eps_per_shape = {}
    corr_combos_per_shape = {}
    for shapeval, data in corrdata.items():
        corr_counts_per_shape[shapeval] = 0
        corr_turns_per_shape[shapeval] = []
        corr_combos_per_shape[shapeval] = []
        corr_eps_per_shape[shapeval] = []
        for comboname, epdata in data.items():
            corr_combos_per_shape[shapeval].append(comboname)
            corr_counts_per_shape[shapeval] += len(data[comboname])
            corr_turns_per_shape[shapeval].append(list(epdata.values())[0])
            episode_name = list(epdata.keys())[0]
            corr_eps_per_shape[shapeval].append(episode_name)


    corrdetails = {"num_corr_eps": len(correpisodes), "num_success": num_success, "num_abort": num_abort, "num_failure": num_failure,
                   "details": {"corr_counts_per_shape": corr_counts_per_shape, "corr_turns_per_shape": corr_turns_per_shape, "corr_eps_per_shape": corr_eps_per_shape, "corr_combos_per_shape": corr_combos_per_shape}}

    if len(correpisodes):
        corrdetails["success"] = round((num_success/len(correpisodes)),3)
        corrdetails["abort"] = round((num_abort/len(correpisodes)),3)
        corrdetails["failure"] = round((num_failure/len(correpisodes)),3)
    else:
        corrdetails["success"] = 0
        corrdetails["abort"] = 0
        corrdetails["failure"] = 0


    
    return corrdetails


def _process_cfq_data(expstats):
    if expstats is None:
        return

    cfqepisodes = expstats["clarification_eps"]
    num_success = 0
    num_abort = 0
    num_failure = 0
    cfqdata = {}
    cfq_success_per_shape = {}    
    for data in cfqepisodes:
        shapeval = list(data.keys())[0]
        if shapeval not in cfqdata:
            cfqdata[shapeval] = {}
        if shapeval not in cfq_success_per_shape:
            cfq_success_per_shape[shapeval] = {"successep": 0, "abortep": 0, "failureep": 0}
        combodata = data[shapeval]
        comboname = list(combodata.keys())[0]
        if comboname not in cfqdata[shapeval]:
            cfqdata[shapeval][comboname] = {}
        if combodata[comboname]["success"]:
            num_success+=1
            cfq_success_per_shape[shapeval]["successep"] += 1
        elif combodata[comboname]["abort"]:
            num_abort+=1
            cfq_success_per_shape[shapeval]["abortep"] += 1
        else:
            num_failure+=1
            cfq_success_per_shape[shapeval]["failureep"] += 1
        combodata[comboname].pop("success")
        combodata[comboname].pop("abort")
        cfqdata[shapeval][comboname].update(combodata[comboname])  

    for shapeval in cfq_success_per_shape:
        toteps = cfq_success_per_shape[shapeval]["successep"] + cfq_success_per_shape[shapeval]["abortep"] + cfq_success_per_shape[shapeval]["failureep"]

        if toteps:
            success = round((cfq_success_per_shape[shapeval]["successep"]/toteps),3)
            abort = round((cfq_success_per_shape[shapeval]["abortep"]/toteps),3)
            failure = round((cfq_success_per_shape[shapeval]["failureep"]/toteps),3)
        else:
            success = 0
            abort = 0
            failure = 0
        cfq_success_per_shape[shapeval]["success"] = success
        cfq_success_per_shape[shapeval]["abort"] = abort
        cfq_success_per_shape[shapeval]["failure"] = failure


    cfq_counts_per_shape = {}
    cfq_turns_per_shape = {}
    cfq_eps_per_shape = {}
    cfq_combos_per_shape = {}
    for shapeval, data in cfqdata.items():
        cfq_counts_per_shape[shapeval] = 0
        cfq_turns_per_shape[shapeval] = []
        cfq_combos_per_shape[shapeval] = []
        cfq_eps_per_shape[shapeval] = []
        for comboname, epdata in data.items():
            cfq_combos_per_shape[shapeval].append(comboname)
            cfq_counts_per_shape[shapeval] += len(data[comboname])
            cfq_turns_per_shape[shapeval].append(list(epdata.values())[0])
            episode_name = list(epdata.keys())[0]
            cfq_eps_per_shape[shapeval].append(episode_name)


    cfqdetails = {"num_cfq_eps": len(cfqepisodes), "num_success": num_success, "num_abort": num_abort, "num_failure": num_failure,
                  "details": {"cfq_counts_per_shape": cfq_counts_per_shape, "cfq_success_per_shape": cfq_success_per_shape,
                   "cfq_turns_per_shape": cfq_turns_per_shape, "cfq_eps_per_shape": cfq_eps_per_shape, "cfq_combos_per_shape": cfq_combos_per_shape}}

    if len(cfqepisodes):
        cfqdetails["success"] = round((num_success/len(cfqepisodes)),3)
        cfqdetails["abort"] = round((num_abort/len(cfqepisodes)),3)
        cfqdetails["failure"] = round((num_failure/len(cfqepisodes)),3)
    else:
        cfqdetails["success"] = 0
        cfqdetails["abort"] = 0
        cfqdetails["failure"] = 0

    return cfqdetails


def _update_skill_usgae_stats(skill_avail_notavail_used_notused_eps, numskillavaileps, numskillunavaileps, skill_avail=True, skill_used=True):

    if skill_avail and skill_used:
        eps_used = skill_avail_notavail_used_notused_eps["avail"]["used"]
        totaleps = numskillavaileps
    elif skill_avail and not skill_used:
        eps_used = skill_avail_notavail_used_notused_eps["avail"]["notused"]
        totaleps = numskillavaileps
    elif not skill_avail and skill_used:
        eps_used = skill_avail_notavail_used_notused_eps["notavail"]["used"]
        totaleps = numskillunavaileps
    else:
        eps_used = skill_avail_notavail_used_notused_eps["notavail"]["notused"]
        totaleps = numskillunavaileps


    eps_success = [ep for ep in eps_used if ep["status"] == "success"]
    eps_abort = [ep for ep in eps_used if ep["status"] == "abort"]
    eps_failure = [ep for ep in eps_used if ep["status"] == "failure"]
    skill_shapestats = {"2": {"count": 0, "success": 0, "abort": 0, "failure": 0, "used_turn":{"first_turn": 0, "last_turn": 0, "any_turn": 0}},
                        "3": {"count": 0, "success": 0, "abort": 0, "failure": 0, "used_turn":{"first_turn": 0, "last_turn": 0, "any_turn": 0}},
                        "4": {"count": 0, "success": 0, "abort": 0, "failure": 0, "used_turn":{"first_turn": 0, "last_turn": 0, "any_turn": 0}},
                        "5": {"count": 0, "success": 0, "abort": 0, "failure": 0, "used_turn":{"first_turn": 0, "last_turn": 0, "any_turn": 0}},
                        "overall": {"count": len(eps_success)+len(eps_abort)+len(eps_failure),
                                   "success": len(eps_success), "abort": len(eps_abort),
                                    "failure": len(eps_failure), "used_turn":{"first_turn": 0, "last_turn": 0, "any_turn": 0}}}
    for ep in eps_used:
        num_shapes = str(ep["num_shapes"])
        if num_shapes in skill_shapestats:
            skill_shapestats[num_shapes]["count"] += 1
            skill_shapestats[num_shapes][ep["status"]] += 1
            if ep["used_turn"]:
                skill_shapestats[num_shapes]["used_turn"][ep["used_turn"]] += 1
    for num_shapes in skill_shapestats:
        if num_shapes == "overall":
            continue
        count = skill_shapestats[num_shapes]["count"]
        if count:
            skill_shapestats[num_shapes]["successrate"] = round((skill_shapestats[num_shapes]["success"]/count),3)
            skill_shapestats[num_shapes]["abortrate"] = round((skill_shapestats[num_shapes]["abort"]/count),3)
            skill_shapestats[num_shapes]["failurerate"] = round((skill_shapestats[num_shapes]["failure"]/count),3)
        else:
            skill_shapestats[num_shapes]["successrate"] = 0
            skill_shapestats[num_shapes]["abortrate"] = 0
            skill_shapestats[num_shapes]["failurerate"] = 0 

        skill_shapestats["overall"]["used_turn"]["first_turn"] += skill_shapestats[num_shapes]["used_turn"]["first_turn"]
        skill_shapestats["overall"]["used_turn"]["last_turn"] += skill_shapestats[num_shapes]["used_turn"]["last_turn"]
        skill_shapestats["overall"]["used_turn"]["any_turn"] += skill_shapestats[num_shapes]["used_turn"]["any_turn"]

    if skill_shapestats["overall"]["count"]:
        skill_shapestats["overall"]["successrate"] = round((skill_shapestats["overall"]["success"]/skill_shapestats["overall"]["count"]),3)
        skill_shapestats["overall"]["abortrate"] = round((skill_shapestats["overall"]["abort"]/skill_shapestats["overall"]["count"]),3)
        skill_shapestats["overall"]["failurerate"] = round((skill_shapestats["overall"]["failure"]/skill_shapestats["overall"]["count"]),3)
    else:
        skill_shapestats["overall"]["successrate"] = 0
        skill_shapestats["overall"]["abortrate"] = 0
        skill_shapestats["overall"]["failurerate"] = 0 

    return skill_shapestats   


def _process_skill_turn_usage(expstats):
    if expstats is None:
        return

    skillavail_success_eps = [epdata["episode_num"] for epdata in expstats["successepsskill"]]
    skillavail_failure_eps = [epdata["episode_num"] for epdata in expstats["failepsskill"]]
    skillavail_abort_eps = [epdata["episode_num"] for epdata in expstats["abortepsskill"]]
    numskillavaileps = len(skillavail_success_eps) + len(skillavail_failure_eps) + len(skillavail_abort_eps)

    skillunavail_success_eps = [epdata["episode_num"] for epdata in expstats["successepsfromscratch"]]
    skillunavail_failure_eps = [epdata["episode_num"] for epdata in expstats["failepsfromscratch"]]
    skillunavail_abort_eps = [epdata["episode_num"] for epdata in expstats["abortepsfromscratch"]]
    numskillunavaileps = len(skillunavail_success_eps) + len(skillunavail_failure_eps) + len(skillunavail_abort_eps)


    epslist = expstats["successepsskill"] + expstats["successepsfromscratch"] + expstats["abortepsskill"] + expstats["abortepsfromscratch"] + expstats["failepsskill"] + expstats["failepsfromscratch"]

    skillturnusage = {"first_turn": 0, "last_turn": 0, "any_turn": 0}
    numskillnotusedeps = 0
    numskillusedeps = 0

    skill_avail_notavail_used_notused_eps = {"avail": {"used": [], "notused": []}, "notavail": {"used": [], "notused": []}}

    for epdata in epslist:
        episode_num = epdata["episode_num"]
        num_shapes = epdata["num_shapes"]
        play_turns = epdata["play_turns"]
        if not epdata["used_skill_1stturn"] and not epdata["used_skill_lastturn"] and not epdata["used_skill_anyturn"]:
            numskillnotusedeps += 1

            if episode_num in skillavail_success_eps:
                skill_avail_notavail_used_notused_eps["avail"]["notused"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "success", "num_shapes": num_shapes, "used_turn": None})
            elif episode_num in skillavail_failure_eps:
                skill_avail_notavail_used_notused_eps["avail"]["notused"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "failure", "num_shapes": num_shapes, "used_turn": None})
            elif episode_num in skillavail_abort_eps:
                skill_avail_notavail_used_notused_eps["avail"]["notused"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "abort", "num_shapes": num_shapes, "used_turn": None})

            elif episode_num in skillunavail_success_eps:
                skill_avail_notavail_used_notused_eps["notavail"]["notused"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "success", "num_shapes": num_shapes, "used_turn": None})
            elif episode_num in skillunavail_failure_eps:
                skill_avail_notavail_used_notused_eps["notavail"]["notused"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "failure", "num_shapes": num_shapes, "used_turn": None})
            elif episode_num in skillunavail_abort_eps:
                skill_avail_notavail_used_notused_eps["notavail"]["notused"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "abort", "num_shapes": num_shapes, "used_turn": None})

        else:
            numskillusedeps+=1
            used_turn = None
            if epdata["used_skill_1stturn"]:
                used_turn = "first_turn"
                skillturnusage["first_turn"] += 1

            elif epdata["used_skill_lastturn"]:
                used_turn = "last_turn"
                skillturnusage["last_turn"] += 1

            elif epdata["used_skill_anyturn"]:
                used_turn = "any_turn"
                skillturnusage["any_turn"] += 1

            if used_turn is None:
                print(f"Skill usage turn is not identified for episode {episode_num} with data {epdata}")

            if episode_num in skillavail_success_eps:
                skill_avail_notavail_used_notused_eps["avail"]["used"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "success", "num_shapes": num_shapes, "used_turn": used_turn})
            elif episode_num in skillavail_failure_eps:
                skill_avail_notavail_used_notused_eps["avail"]["used"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "failure", "num_shapes": num_shapes, "used_turn": used_turn})
            elif episode_num in skillavail_abort_eps:
                skill_avail_notavail_used_notused_eps["avail"]["used"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "abort", "num_shapes": num_shapes, "used_turn": used_turn})

            elif episode_num in skillunavail_success_eps:
                skill_avail_notavail_used_notused_eps["notavail"]["used"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "success", "num_shapes": num_shapes, "used_turn": used_turn})
            elif episode_num in skillunavail_failure_eps:
                skill_avail_notavail_used_notused_eps["notavail"]["used"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "failure", "num_shapes": num_shapes, "used_turn": used_turn})
            elif episode_num in skillunavail_abort_eps:
                skill_avail_notavail_used_notused_eps["notavail"]["used"].append({"episode_num":episode_num, "play_turns": play_turns, "status": "abort", "num_shapes": num_shapes, "used_turn": used_turn})


    skill_shapestats_avail_used = _update_skill_usgae_stats(skill_avail_notavail_used_notused_eps, numskillavaileps, numskillunavaileps, skill_avail=True, skill_used=True)

    skill_shapestats_avail_notused = _update_skill_usgae_stats(skill_avail_notavail_used_notused_eps, numskillavaileps, numskillunavaileps, skill_avail=True, skill_used=False)    

    skill_shapestats_notavail_used = _update_skill_usgae_stats(skill_avail_notavail_used_notused_eps, numskillavaileps, numskillunavaileps, skill_avail=False, skill_used=True)    

    skill_shapestats_notavail_notused = _update_skill_usgae_stats(skill_avail_notavail_used_notused_eps, numskillavaileps, numskillunavaileps, skill_avail=False, skill_used=False)


    print(f"Total skillavail eps: {numskillavaileps}, skillunavaileps: {numskillunavaileps}")
    print(f"TotalEps used skill: {numskillusedeps}, TotalEps not used skill: {numskillnotusedeps}")
    print(f'TotalEps used skill when skill available: {skill_shapestats_avail_used["overall"]["count"]}, TotalEps not used skill when skill available: {skill_shapestats_avail_notused["overall"]["count"]}')
    print(f'TotalEps used skill when skill available success: {skill_shapestats_avail_used["overall"]["successrate"]}, TotalEps not used skill when skill available success: {skill_shapestats_avail_notused["overall"]["successrate"]}')
    print(f'TotalEps used skill when skill not available: {skill_shapestats_notavail_used["overall"]["success"]}, TotalEps not used skill when skill not available: {skill_shapestats_notavail_notused["overall"]["count"]}')
    print(f'TotalEps used skill when skill not available success: {skill_shapestats_notavail_used["overall"]["successrate"]}, TotalEps not used skill when skill not available success: {skill_shapestats_notavail_notused["overall"]["successrate"]}')
    
    skillusage_turns = {"total_skill_avail_eps": numskillavaileps,
                        "total_skill_unavail_eps": numskillunavaileps,     
                        "total_eps_used_skill": numskillusedeps,
                        "total_eps_used_skill_success": skill_shapestats_avail_used["overall"]["success"]+skill_shapestats_notavail_used["overall"]["success"],
                        "total_eps_not_used_skill": numskillnotusedeps,
                        "total_eps_not_used_skill_success": skill_shapestats_avail_notused["overall"]["success"]+skill_shapestats_notavail_notused["overall"]["success"],
                        "skill_avail_used_rate": round((skill_shapestats_avail_used["overall"]["count"]/numskillavaileps),2) if numskillavaileps else 0,
                        "skill_avail_notused_rate": round((skill_shapestats_avail_notused["overall"]["count"]/numskillavaileps),2) if numskillavaileps else 0,
                        "skill_notavail_used_rate": round((skill_shapestats_notavail_used["overall"]["count"]/numskillunavaileps),2) if numskillunavaileps else 0,
                        "skill_notavail_notused_rate": round((skill_shapestats_notavail_notused["overall"]["count"]/numskillunavaileps),2) if numskillunavaileps else 0,
                        "skill_avail_used": skill_shapestats_avail_used,
                       "skill_avail_notused": skill_shapestats_avail_notused,
                       "skill_notavail_used": skill_shapestats_notavail_used,
                       "skill_notavail_notused": skill_shapestats_notavail_notused}

    return skillusage_turns


def _process_unavailskill_episodes(expstats):
    if expstats is None:
        return

    skillunavaileps = expstats["skill_unavail_eps"]

    shapedata = {}
    for shapecnt in skillunavaileps:
        shapeval = list(shapecnt.keys())[0]
        if shapeval not in shapedata:
            shapedata[shapeval] = {}
        combodata = shapecnt[shapeval]
        comboname = list(combodata.keys())[0]
        if comboname not in shapedata[shapeval]:
            shapedata[shapeval][comboname] = {}
        shapedata[shapeval][comboname].update(combodata[comboname])

    totalmissedskills = 0
    combocounts = {}
    combonamecounts = {}
    for shapeval, data in shapedata.items():
        totalmissedskills += len(list(data.keys()))
        combocounts[shapeval] = len(data)
        combonamecounts[shapeval] = {}
        for comboname, epdata in data.items():
            if comboname not in combonamecounts[shapeval]:
                combonamecounts[shapeval][comboname] = 0
            combonamecounts[shapeval][comboname] += len(epdata)

    print(f"Missed skills for {totalmissedskills} combos")
    skillunavailcombodata = {"num_combos":totalmissedskills, "combo_counts_per_shape": combocounts,
                             "combonames_counts": combonamecounts }
    return skillunavailcombodata

def _process_skillusage(expstats):
    if expstats is None:
        return

    totaleps = expstats["num_episodes"]
    totalskills = expstats["num_skills"]
    totaleps_skill_sum = len(expstats["successepsskill"]) + len(expstats["abortepsskill"]) + len(expstats["failepsskill"])
    totaleps_skill = expstats["skillavailepscnt"]
    if totaleps_skill != totaleps_skill_sum:
        print(f"Diff between eps skill totaleps_skill: {totaleps_skill}, totaleps_skill_sum: {totaleps_skill_sum}")
        input()
    totaleps_nonskill_sum = len(expstats["successepsfromscratch"]) + len(expstats["abortepsfromscratch"]) + len(expstats["failepsfromscratch"])
    totaleps_nonskill = expstats["skillnotavailepscnt"]
    if totaleps_nonskill != totaleps_nonskill_sum:
        print(f"Diff between eps skill totaleps_nonskill: {totaleps_nonskill}, totaleps_nonskill_sum: {totaleps_nonskill_sum}")
        input()

    skillepnums = []
    for epstatus in ["successepsskill", "abortepsskill", "failepsskill"]:
        for epdata in expstats[epstatus]:
            epnum = epdata["episode_num"]#list(epdata.keys())[0]
            skillepnums.append(epnum)


    eps_skill_avail = {"num_episodes": totaleps_skill, 
                         "num_success": len(expstats["successepsskill"]),
                         "num_abort": len(expstats["abortepsskill"]),
                         "num_failure": len(expstats["failepsskill"]),
                         "overall_success": round((len(expstats["successepsskill"])/totaleps), 3),}
    if totaleps_skill:
        eps_skill_avail["success"] = round((len(expstats["successepsskill"])/totaleps_skill), 3)
        eps_skill_avail["abort"] = round((len(expstats["abortepsskill"])/totaleps_skill), 3)
        eps_skill_avail["failure"] = round((len(expstats["failepsskill"])/totaleps_skill), 3)
        
    else:
        eps_skill_avail["success"] = 0
        eps_skill_avail["abort"] = 0
        eps_skill_avail["failure"] = 0

    eps_skill_notavail = {"num_episodes": totaleps_nonskill, 
                         "num_success": len(expstats["successepsfromscratch"]),
                         "num_abort": len(expstats["abortepsfromscratch"]),
                         "num_failure": len(expstats["failepsfromscratch"]),
                         "overall_success": round((len(expstats["successepsfromscratch"])/totaleps), 3),}
    if totaleps_nonskill:
        eps_skill_notavail["success"] = round((len(expstats["successepsfromscratch"])/totaleps_nonskill), 3)
        eps_skill_notavail["abort"] = round((len(expstats["abortepsfromscratch"])/totaleps_nonskill), 3)
        eps_skill_notavail["failure"] = round((len(expstats["failepsfromscratch"])/totaleps_nonskill), 3)
        
    else:
        eps_skill_notavail["success"] = 0
        eps_skill_notavail["abort"] = 0
        eps_skill_notavail["failure"] = 0

    skillunavailcombodata = _process_unavailskill_episodes(expstats)
    eps_skill_notavail["details"] = skillunavailcombodata

    eps_noskill = {"clp": {}, "gpt": {}}
    totaleps_noskill_clpskill_sum = len(expstats["noskills"]["clp"]["successeps"]) + len(expstats["noskills"]["clp"]["aborteps"]) + len(expstats["noskills"]["clp"]["faileps"])

    totaleps_noskill_gptskill_sum = len(expstats["noskills"]["gpt"]["successeps"]) + len(expstats["noskills"]["gpt"]["aborteps"]) + len(expstats["noskills"]["gpt"]["faileps"])


    eps_noskill["clp"] = {"num_skill_avail_eps": totaleps_noskill_clpskill_sum, "num_success": len(expstats["noskills"]["clp"]["successeps"]),
                         "num_abort": len(expstats["noskills"]["clp"]["aborteps"]),
                         "num_failure": len(expstats["noskills"]["clp"]["faileps"]),}
    if totaleps_noskill_clpskill_sum:
        eps_noskill["clp"]["success"] = round((len(expstats["noskills"]["clp"]["successeps"])/totaleps_noskill_clpskill_sum), 3)
        eps_noskill["clp"]["abort"] = round((len(expstats["noskills"]["clp"]["aborteps"])/totaleps_noskill_clpskill_sum), 3)
        eps_noskill["clp"]["failure"] = round((len(expstats["noskills"]["clp"]["faileps"])/totaleps_noskill_clpskill_sum), 3)

    eps_noskill["gpt"] = {"num_skill_avail_eps": totaleps_noskill_gptskill_sum, "num_success": len(expstats["noskills"]["gpt"]["successeps"]),
                         "num_abort": len(expstats["noskills"]["gpt"]["aborteps"]),
                         "num_failure": len(expstats["noskills"]["gpt"]["faileps"]),}
    if totaleps_noskill_gptskill_sum:
        eps_noskill["gpt"]["success"] = round((len(expstats["noskills"]["gpt"]["successeps"])/totaleps_noskill_gptskill_sum), 3)
        eps_noskill["gpt"]["abort"] = round((len(expstats["noskills"]["gpt"]["aborteps"])/totaleps_noskill_gptskill_sum), 3)
        eps_noskill["gpt"]["failure"] = round((len(expstats["noskills"]["gpt"]["faileps"])/totaleps_noskill_gptskill_sum), 3)        


    noskill_skillepnums = {"clp": [], "gpt": []}
    for model in ["clp", "gpt"]:
        for epstatus in ["successeps", "aborteps", "faileps"]:
            for epdata in expstats["noskills"][model][epstatus]:
                epnum = list(epdata.keys())[0]
                noskill_skillepnums[model].append(epnum)
    noskill_skillepnums["clp"] = sorted(noskill_skillepnums["clp"])
    noskill_skillepnums["gpt"] = sorted(noskill_skillepnums["gpt"])


    eps_skill_details = {"num_skill_avail_eps": totaleps_skill, "num_skill_nonavail_eps": totaleps_nonskill,
                         "per_skill_avail_eps": round((totaleps_skill/totaleps),3),
                          "per_skill_nonavail_eps": round((totaleps_nonskill/totaleps),3),
                         "skillavaildata": eps_skill_avail,
                         "skillnonavaildata": eps_skill_notavail, "noskilldata": eps_noskill, "skillusageturns": None }

    print(f"TotalSkillAvailEps: {totaleps_skill}, ActualAvailSkills_Eps: ({totalskills}, {totalskills*3}), SkillNonAvailEps: {totaleps_nonskill}")
    if "success" in eps_skill_avail and "success" in eps_skill_notavail:
        print(f'eps_skill_avail[success,abort,failure]: {eps_skill_avail["success"]}, {eps_skill_avail["abort"]}, {eps_skill_avail["failure"]}')
        print(f'eps_skill_notavail[success,abort,failure]: {eps_skill_notavail["success"]}, {eps_skill_notavail["abort"]}, {eps_skill_notavail["failure"]}')
    print(f'eps_skill_avail[overall]: {eps_skill_avail["overall_success"]}, eps_skill_notavail[overall]: {eps_skill_notavail["overall_success"]}')

    skillusageturns = _process_skill_turn_usage(expstats)
    eps_skill_details["skillusageturns"] = skillusageturns

    return eps_skill_details, skillepnums, noskill_skillepnums

def _process_overall(expstats):
    if expstats is None:
        return

    totaleps = expstats["num_episodes"]
    totalsuccess = len(expstats["successeps"])
    totalabort = len(expstats["aborteps"])
    totalfailure = len(expstats["faileps"])
    totalskills = expstats["num_skills"]
    #print(f"Total Episodes: {totaleps}, Success: {totalsuccess}, Abort: {totalabort}, Failure: {totalfailure}")

    overall_stats = {"num_episodes": totaleps, "success_eps": totalsuccess, "abort_eps": totalabort, "fail_eps": totalfailure,
                     "successrate": round((totalsuccess/totaleps),3), "abortrate": round((totalabort/totaleps),3),
                     "failurerate": round((totalfailure/totaleps),3), "num_skills": totalskills,
                     }

    eplist = []
    for ep in expstats["aborteps"]:
        eplist.append(list(ep.keys())[0])
    overall_stats["abortepslist"] = eplist

    eplist = []
    for ep in expstats["faileps"]:
        eplist.append(list(ep.keys())[0])
    overall_stats["failepslist"] = eplist               

    print(f"Total Episodes: {totaleps}, Success: {totalsuccess}, Abort: {totalabort}, Failure: {totalfailure}")
    print(f'Success: {overall_stats["successrate"]}, Abort: {overall_stats["abortrate"]}, Failure: {overall_stats["failurerate"]}')
    
    return overall_stats


def checkdiffbwskillstest(episode_path, combonamedict):
    interavail = isinstanceinfoavailable(episode_path)
    if not interavail:
        return    

    interaction_data = {}
    interactions_path = os.path.join(episode_path, "interactions.json")
    if os.path.exists(interactions_path):
        interactions = read_json_file(interactions_path) or {}
        skillcode = interactions["Evaluation"]["skills_code"]
        comboname = interactions["Evaluation"]["boardinfo"]["regular"]["combo_name"]
        if comboname in skillcode:
            combonamedict["skillavail"].add(comboname)
        else:
            if comboname == "wbvbvns":
                print(episode_path)
                input()
            combonamedict["skillnotavail"].add(comboname)
    else:
        pass


def _process_combo_diff(expstats, combonamestats):
    if expstats is None or combonamestats is None:
        return

    skillfilenames = list(expstats["skillsfilename"].keys())
    if len(skillfilenames) > 1:
        print(f"More than one skillname file in the instances! {skillfilenames}")

    skilldata_base = read_json_file(f"resources/data/en/{skillfilenames[0]}")
    numskill_base = len(skilldata_base)
    print(f"Base skills available from the file: {skillfilenames[0]} -> {numskill_base}")
    numskill_instances = len(combonamestats["skillavail"])
    print(f"Skills available from the interactions file: -> {numskill_instances}")

    if set(expstats["skillavailcombos"]) != combonamestats["skillavail"]:
        print(f'Difference in notavailcombos: {set(expstas["skillavailcombos"]) - combonamestats["skillavail"]}')
    else:
        print("No difference in avail skills")

    if set(expstats["skillnotavailcombos"]) != combonamestats["skillnotavail"]:
        print(f'Difference in notavailcombos: {set(expstas["skillnotavailcombos"]) - combonamestats["skillnotavail"]}')        
    else:
        print("No difference in not avail skills")


    skill_inbase_notincode = []
    for skill in skilldata_base:
        #if skill not in combonamestats["skillavail"] and skill not in combonamestats["skillnotavail"]:
        if skill not in expstats["skillavailcombos"] and skill not in expstats["skillnotavailcombos"]:
            skill_inbase_notincode.append(skill)

    #The difference would be because for this particular comboname, all the episodes would be aborted and hence it is not in expstats dict
    print(skill_inbase_notincode)



def compute_scores(base_dir: str, verbose: bool = True) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        with open(f"resources/data/en/learnedskills_clp.json", 'r', encoding='utf-8') as file:
            clpskills = json.load(file)

        with open(f"resources/data/en/learnedskills_gpt.json", 'r', encoding='utf-8') as file:
            gptskills = json.load(file)

    except Exception as e:
        # Read these skills so that we can compute success, costs for No Skills scenario so as to compare with the Skills based scenario
        print(f"Error loading skills data: {e}")
        input()
        clpskills = {}
        gptskills = {}

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

                accuracy_data: List[float] = []
                failed_episodes: List[str] = []
                aborted_episodes: List[str] = []
                reuse_success_episodes: List[int] = []
                reuse_turns: List[int] = []
                overall_success: int = 0
                from_scratch_episodes: List[int] = []
                cfq_episodes = {"present": [], "not_present": []}

                episodes = [d for d in os.listdir(exp_path) if os.path.isdir(os.path.join(exp_path, d))]
                num_episodes = len(episodes)
                expstats = {"successeps": [], "aborteps": [], "faileps": [], "clarification_eps": [],
                            "correction_eps": [], "undo_eps":[], "num_turns": [], "num_skills": 0, "skill_unavail_eps": [],
                            "skill_oracle_eps": [], "successepsfromscratch": [], "abortepsfromscratch": [],
                            "failepsfromscratch": [], "successepsskill": [], "abortepsskill": [], "failepsskill": [],
                            "gencode": [], "geninstructions": [], "num_turns_code_gen": [], "num_episodes": num_episodes,
                            "skillavailepscnt": 0, "skillnotavailepscnt": 0, "skillsfilename": {}, "skillavailcombos": [],
                            "skillnotavailcombos": [], "skillandtargetcellsdiscrep": {"success": [], "abort": [], "failure": []},
                            "noskills": {"clp": {"successeps": [], "aborteps": [], "faileps": []},
                                          "gpt": {"successeps": [], "aborteps": [], "faileps": []}},
                            "shape_stats":{2: {"successeps": 0, "aborteps": 0, "faileps": 0},
                                           3: {"successeps": 0, "aborteps": 0, "faileps": 0},
                                           4: {"successeps": 0, "aborteps": 0, "faileps": 0},
                                           5: {"successeps": 0, "aborteps": 0, "faileps": 0}},}
                combonamestats = {"skillavail": set(), "skillnotavail": set()}

                for episode in episodes:
                    episode_path = os.path.join(exp_path, episode)
                    process_episode(episode_path, expstats, clpskills, gptskills)
                    #checkdiffbwskillstest(episode_path, combonamestats)
                print(f"Finished processing {model}")
                overall_stats = _process_overall(expstats)
                eps_skill_details, skillepnums, noskill_skillepnums = _process_skillusage(expstats)
                cfq_details = _process_cfq_data(expstats)
                corr_details = _process_correction_data(expstats)
                skilldescp_details = _process_skill_discrepancy(expstats)

                with open(f"{base_dir}/{model}_{exp}_skillavaileps.json", 'w', encoding='utf-8') as file:
                    json.dump(skillepnums, file, indent=4)

                with open(f"{base_dir}/{model}_{exp}_noskill_eps_clp.json", 'w', encoding='utf-8') as file:
                    json.dump(noskill_skillepnums["clp"], file, indent=4)

                with open(f"{base_dir}/{model}_{exp}_noskill_eps_gpt.json", 'w', encoding='utf-8') as file:
                    json.dump(noskill_skillepnums["gpt"], file, indent=4)

                #_process_combo_diff(expstats, combonamestats)
                results[game][model][exp] = {"overall_stats": overall_stats, "skill_data": eps_skill_details,
                                             "clarifications": cfq_details, "corrections": corr_details,}

    with open(f"{base_dir}/overallstats.json", 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Compute overall scores from experiment directories")
    parser.add_argument("base_dir", nargs="?",
                         default="rp_clpskills_human_clp_4", help="Base directory containing model results")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose printing")
    args = parser.parse_args()

    compute_scores(args.base_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()
