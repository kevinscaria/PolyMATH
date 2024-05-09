import pandas as pd
import numpy as np
import time

get_ipython().run_line_magic('pip', 'install -q -U google-generativeai')

import base64
import tqdm

do_gemini = True

import google.generativeai as genai
genai.configure(api_key='')

for m in genai.list_models():
    print(m.name,m.description)

from PIL import Image

pre_image_prompt = '''Provide descriptions for the following images.'''
post_image_prompt = '''Output descriptions as a numbered list.'''

precontext = '''This is the context for a mathematical problem.'''
postcontext = '''Based on the information above, answer the following question.'''
preq = '''Question instruction: '''
postq = '''Output only the correct answer option.'''

def gen_template(precontext,postcontext,preq,postq,contextpaths,imgpaths):

    imgs = []
    contexts = []

    for im in imgpaths:
        imgs.append(Image.open(im))
    for c in contextpaths:
        contexts.append(Image.open(c))

    # template = [pre_image_prompt] + imgs + [post_image_prompt] # for testing/debugging purposes
    template = [precontext] + contexts + [postcontext,preq] + imgs + [postq]
    return template


def gemini_response(contextpaths,imgpaths):
    time.sleep(20)
    mod = 'gemini-pro-vision'

    gmodel = genai.GenerativeModel(mod)  # gemini-1.0-pro-vision-latest
    temp = gen_template(contextpaths=contextpaths,imgpaths=imgpaths)
    
    response = gmodel.generate_content(temp,stream=True)
    response.resolve()
    try:
        rsp = response.text
        # print('worked')
    except: 
        rsp = response.prompt_feedback
        # print('issue')
    return rsp


anndfpath = ''
opfile = ''

annotation_df = pd.read_csv(anndfpath)
gemini_inferences = []
for i,r in tqdm.tqdm(annotation_df.iterrows(),total=annotation_df.shape[0]):

    # imagepaths: 
    contexts = r['context']
    question = r['question']
    gemini_inferences.append(gemini_response(contextpaths=contexts,
                                                imgpaths=question))


annotation_df['gemini_inferences'] = gemini_inferences
annotation_df.to_csv(opfile,index=False)
