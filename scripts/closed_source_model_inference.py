# Closed Source Model Inference via API
import time
import os
import pandas as pd
from tqdm.auto import tqdm
from ast import literal_eval
from inference_models import GeminiVisionInference

root_path = "../datastore/QP_Karnataka NTSE Stage1 (2017-18) MAT"
ss_path =  os.path.join(root_path,"screenshots")
annotation_df_path = os.path.join(root_path,"annotations.csv")
output_file_path = os.path.join(root_path,"annotations_w_gemini_response.csv")
annotation_df = pd.read_csv(annotation_df_path)
# print(annotation_df.columns)
# Gemini Inference
gemini_model_client = GeminiVisionInference(sleep_time=30)
gemini_inferences = []
annotation_df.fillna('',inplace=True)
for idx, row in tqdm(annotation_df.iterrows(),total=annotation_df.shape[0]):

    # image paths:
    contexts = [os.path.join(ss_path,i) for i in literal_eval(row['context-input']) if row['context-input'] != '']
    question = [os.path.join(ss_path,i) for i in literal_eval(row['input_image_location-input']) ]

    gemini_inferences.append(gemini_model_client.gemini_response(context_paths=contexts,
    img_paths=question))
    if idx%10 == 0  and idx !=0 :
        print('time out')
        time.sleep(30)

annotation_df['gemini_inferences'] = gemini_inferences
annotation_df.to_csv(output_file_path, index=False)