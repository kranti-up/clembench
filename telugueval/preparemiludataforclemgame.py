import os
import re
import pandas as pd
import json

BASE_DIR = "../testset/"
TEST_MILU_FILE_NAME = "milu/milu_processed_data_subset_annotated.xlsx"
TEST_INCLUDE_FILE_NAME = "include/include44-base-Telsubset_annotated.xlsx"
SEED = 42


class CleanTestData:
    def __init__(self):
        pass

    def fix_malformed_list_milu(malformed_str):
        # Use regex to extract text inside quotes while preserving spaces
        #corrected_list = re.findall(r'"(.*?)"', malformed_str)
        input_string = malformed_str.replace('["', '')
        input_string = input_string.replace('"]', '')
        input_string = input_string.replace('" "', "\t")
        corrected_list = input_string.split("\t")
        if not len(corrected_list) ==4:
            print("This one doesn't have 4 choices: ", corrected_list)

        return corrected_list
    
    def fix_malformed_list_include(malformed_str):
        # Use regex to extract text inside quotes while preserving spaces
        clean_text = malformed_str.strip('[]')
        clean_text = re.sub(r"\\u200c", "", clean_text)
        corrected_list = re.findall(r"'(.*?)'", clean_text)
        if not len(corrected_list) ==4:
            print("This one doesn't have 4 choices: ", corrected_list)
        return corrected_list
    
    def apply_constraints(self, df, constraints):

        df_processed = df[df['choices'].apply(len) == 4]

        if constraints[0] == "questions-clean":
            df_processed = df_processed[df_processed[constraints[1]] == constraints[2]]

        return df_processed


    def run(self, filenames):
        number_letter_mapping_milu = {"A": 1, "B": 2, "C": 3, "D": 4}
        
        for filename in filenames:
            if "milu" in filename or "include" in filename:
                filepath = os.path.join(BASE_DIR, filename)
            else:
                print("Invalid filename")
                return
            
            df = pd.read_excel(filepath)
            print(f"Number of rows in the file:{filename} - {df.shape[0]}")
            json_data = []
            
            if "milu" in filename:
                df['choices'] = df['choices'].apply(CleanTestData.fix_malformed_list_milu)
            elif "include" in filename:
                df['choices'] = df['choices'].apply(CleanTestData.fix_malformed_list_include)


            for constraint in [("choices-clean", "4"), ("questions-clean", "concerns - K", "NoConcerns")]:
                df_processed = self.apply_constraints(df, constraint)
                df_processed['answer'] = df_processed['answer'].apply(lambda x: number_letter_mapping_milu.get(x, int(x)))
                df_processed['question'] = df_processed.apply(lambda row: f"{row['question']}\n1. {row['choices'][0]}\n2. {row['choices'][1]}\n3. {row['choices'][2]}\n4. {row['choices'][3]}", axis=1)

                json_data = df_processed[['question', 'choices', 'answer']].rename(columns={'answer': 'answer_gt'}).to_dict(orient='records')

                outfile = "telugueval/resources/nlu/qna/mcq/te/" + filename.split('/')[-1].split('.')[0] + "_clemgame_" + constraint[0] + ".json"
                print(f"Processed rows in the file:{outfile} - {len(json_data)}")            
                with open(outfile, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                print(f"Json data saved to file: {outfile}")


if __name__ == "__main__":
    filenames = [TEST_MILU_FILE_NAME, TEST_INCLUDE_FILE_NAME]
    CleanTestData().run(filenames)




