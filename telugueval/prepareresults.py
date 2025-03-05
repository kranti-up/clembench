import os
import json
import pandas as pd
import numpy as np




def compute_scores(base_dir):
    accuracy_data = {}

    # Iterate through each model directory
    for model in os.listdir(base_dir):
        # Get the first part of the model name (before --)
        model_base_name = model.split('--')[0]
        model_path = os.path.join(base_dir, model)
        #if "70B" in model_base_name:
        #    continue
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

    # Prepare the table data with mean and standard error
    table_data = {}
    std_error_data = {}
    for experiment, models in accuracy_data.items():
        table_data[experiment] = {}
        std_error_data[experiment] = {}
        for model, accuracies in models.items():
            # Calculate mean
            mean_acc = np.mean(accuracies)
            # Calculate standard error
            std_error = np.std(accuracies, ddof=1) / np.sqrt(len(accuracies))
            
            table_data[experiment][model] = mean_acc
            std_error_data[experiment][model] = std_error

    # Create DataFrames for both mean and standard error
    df_mean = pd.DataFrame(table_data).T.fillna(0)
    df_std = pd.DataFrame(std_error_data).T.fillna(0)

    # Round both DataFrames
    df_mean = df_mean.round(3)
    df_std = df_std.round(3)

    # Combine mean and standard error in the format: mean ± std_err
    df_combined = df_mean.astype(str) + ' ± ' + df_std.astype(str)

    # Display the results
    print("\nAccuracy Results (mean ± standard error):")
    print("================")
    print(df_combined)

    # Save combined results to JSON
    combined_results = {
        'mean': df_mean.to_dict(),
        'std_error': df_std.to_dict()
    }
    with open(f"{base_dir}/accuracy_results.json", "w", encoding="utf-8") as f:
        json.dump(combined_results, f, indent=4)

    # Save as LaTeX table
    latex_table = df_combined.to_latex(
        float_format="%.3f",  # Format numbers to 3 decimal places
        caption="Accuracy Results Across Different Models",  # Optional caption
        label="tab:accuracy_results",  # Optional label
        bold_rows=True,  # Make row headers (experiment names) bold
        position='h'  # Positioning hint for LaTeX
    )

    # Save to LaTeX file
    with open(f"{base_dir}/accuracy_results.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)


compute_scores('/home/admin/Desktop/codebase/cocobots/mindfuleval_repo/mindfuleval/clemgames/results/')