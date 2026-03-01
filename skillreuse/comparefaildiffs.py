import os
import json
import numpy as np



class CompareResultsDiff:
    def __init__(self):
        pass

    def readfile(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    

    def run(self, filename1, filename2):
        data1 = self.readfile(filename1)
        data2 = self.readfile(filename2)

        newfailseps = []
        # Assuming the structure is {game: {model: {exp: {overall_stats: {...}}}}}
        for game in data1:
            for model in data1[game]:
                for exp in data1[game][model]:
                    f1faileps = data1[game][model][exp]["failures"]
                    f2faileps = data2[game][model][exp]["failures"]

                    # Compare the overall stats and print differences
                    print(f"Comparing results for Game: {game}, Model: {model}, Experiment: {exp}")
                    for ep in f2faileps:
                        if ep not in f1faileps:
                            newfailseps.append(ep)

        print(f"Total New failed episodes are: {len(newfailseps)}")
        with open("newfailseps.json", 'w', encoding='utf-8') as file:
            json.dump(newfailseps, file, indent=4)

    def checkforskills(self, filename1, filename2):
        data1 = self.readfile(filename1)
        data2 = self.readfile(filename2)

        missedskills = []
        for comboname in data1:
            if comboname not in data2:
                #print(f"Combo {comboname} is missing in second file")
                missedskills.append(comboname)

        print(f"Total missed skills are: {len(missedskills)}")
        with open("missedskills_1.json", 'w', encoding='utf-8') as file:
            json.dump(missedskills, file, indent=4)
            



if __name__ == "__main__":
    compare = CompareResultsDiff()
    #compare.run("results_old/rp1_clpskills_clp/overallstats.json", "rp_clpskills_clp_3/overallstats.json")
    compare.checkforskills("resources/data/en/old/learnedskills_clp_lat.json", "resources/data/en/learnedskills_clp.json")