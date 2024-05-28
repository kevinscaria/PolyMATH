# Closed Source Model Inference via API


import pandas as pd
from tqdm.auto import tqdm

from inference_models import GeminiVisionInference

annotation_df_path = ""
output_file_path = ""
annotation_df = pd.read_csv(annotation_df_path)

# Gemini Inference
gemini_model_client = GeminiVisionInference(sleep_time=30)
gemini_inferences = []
for idx, row in tqdm(annotation_df.iterrows(),total=annotation_df.shape[0]):

    # image paths:
    contexts = row['context']
    question = row['question']
    gemini_inferences.append(gemini_model_client.gemini_response(context_paths=contexts,
                                                                 img_paths=question))

annotation_df['gemini_inferences'] = gemini_inferences
annotation_df.to_csv(output_file_path, index=False)