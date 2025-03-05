import os
import json
import pandas as pd




def compute_scores(base_dir):
    accuracy_data = {}

    # Iterate through each model directory
    for model in os.listdir(base_dir):
        # Get the first part of the model name (before --)
        model_base_name = model.split('--')[0]
        model_path = os.path.join(base_dir, model)
        
        if os.path.isdir(model_path):
            # Iterate through each game directory
            for game in os.listdir(model_path):
                game_path = os.path.join(model_path, game)
                if os.path.isdir(game_path):
                    # Iterate through each experiment directory
                    for experiment in os.listdir(game_path):
                        experiment_path = os.path.join(game_path, experiment)
                        if os.path.isdir(experiment_path):
                            # Initialize accuracy list for the current experiment
                            if experiment not in accuracy_data:
                                accuracy_data[experiment] = {}
                            # Iterate through each episode directory
                            for episode in os.listdir(experiment_path):
                                episode_path = os.path.join(experiment_path, episode)
                                scores_file = os.path.join(episode_path, 'scores.json')
                                # Read the scores.json file
                                if os.path.isfile(scores_file):
                                    with open(scores_file, 'r', encoding='utf-8') as f:
                                        scores = json.load(f)
                                        # Get the accuracy value
                                        accuracy = scores.get('episode scores', {}).get('Accuracy', None)
                                        if accuracy is not None:
                                            # Store the accuracy using the base model name
                                            accuracy_data[experiment][model_base_name] = accuracy_data[experiment].get(model_base_name, []) + [accuracy]

    # Prepare the table data
    table_data = {}
    for experiment, models in accuracy_data.items():
        table_data[experiment] = {model: sum(acc) / len(acc) for model, acc in models.items()}

    # Convert to DataFrame
    df = pd.DataFrame(table_data).T.fillna(0)

    df = df.round(2)

    # Display the overall accuracy table
    print("\nAccuracy Results:")
    print("================")
    print(df)

    # Save as LaTeX table
    latex_table = df.to_latex(
        float_format="%.2f",  # Format numbers to 2 decimal places
        caption="Accuracy Results Across Different Models",  # Optional caption
        label="tab:accuracy_results",  # Optional label
        bold_rows=True,  # Make row headers (experiment names) bold
        position='h'  # Positioning hint for LaTeX
    )

    # Save to LaTeX file
    with open(f"{base_dir}/accuracy_results.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)

    # Convert to JSON and save
    df.to_json(f"{base_dir}/accuracy_results.json", orient="index", indent=4)


compute_scores('/home/admin/Desktop/codebase/cocobots/mindfuleval_repo/mindfuleval/clemgames/results/')