import os
import uuid
import json
import argparse
import glob
import shutil
import pandas as pd
from tqdm import tqdm
import jsonlines

"""
This script contains the set of utility functions
useful for the annotator
"""

parser = argparse.ArgumentParser(description='Prepare uniform directory structure')
parser.add_argument('-m','--mode', help='The annotations utility mode', required=False)
parser.add_argument('-pp','--paper_path', help='The name of paper', required=False)
parser.add_argument('-dp','--datastore_path', help='The path of datastore', required=True)
parser.add_argument('-an','--annotator_name', help='The name of annotator', required=False)
parser.add_argument('-u','--update', help='Update an entry', required=False, default=False)
args = vars(parser.parse_args())

def create_annotations_helper(paper_path, paper_id):
    qdir = 'screenshots'
    cdir = 'screenshots'

    # Extract all screenshots into respective lists
    files = [os.path.basename(p) for p in glob.glob(os.path.join(paper_path, qdir,'*.png'))]
    contexts = [os.path.basename(p) for p in glob.glob(os.path.join(paper_path, cdir,'*.png')) \
                if os.path.basename(p)[0]=='c']
    questions = pd.Series([p.split('_')[0] for p in files if p[0]=='q']).unique()  

    # Fields for automatic annotation
    sample_ids = questions
    paper_ids = [paper_id]*len(questions)
    imgpaths = []
    contexts = []
    input_text_parsed = []

    # Fields for manual annotation
    instruction=[]
    explanation=[]
    final_answer=[]
    final_answer_range=[]
    page_number=[]

    for i,q in tqdm(enumerate(questions),total=len(questions)):
    
        imgs = glob.glob(os.path.join(paper_path,qdir,f'{q}*.png')) # list of all images for this q
        imgpaths.append([os.path.basename(p) for p in imgs]) # in case single question is split into multiple screenshots
        imgex = imgpaths[-1][-1]
        
        if('c' in imgex): # i.e. context exists for this question
            cfile = imgex.split('_')[-1]
            if not os.path.isfile(os.path.join(paper_path,cdir,cfile)):
                print('context not found!')
                contexts.append('ERROR')
            else:
                contexts.append(cfile)
        else: contexts.append('NULL')
            
        
        input_text_parsed.append('')
        
        instruction.append('')
        final_answer.append('')
        final_answer_range.append('')
        page_number.append('')
        explanation.append('')

    # Create schema for annotations table
    annotation_file = pd.DataFrame(
        data={
            "paper_id-input":paper_ids,
            "sample_id-input":sample_ids,
            "page_number-input":page_number,
            "input_image_location-input":imgpaths,
            "section_instruction-input":instruction,
            "context-input":contexts,
            "input_text_parsed-input":input_text_parsed,
            "explanation-output":explanation,
            "final_answer-output":final_answer,
            "final_answer_range-output":final_answer_range
            }
        )
    return annotation_file

def get_dict_array(ann_df):
    # getting nested-index JSON from annotation csv
    ann_df = ann_df.astype(str)
    opdct=[]

    for i,r in ann_df.iterrows():
        dct={}
        dct['input']={}
        dct['output']={}

        for k in list(ann_df.columns):
            col,splits = k.split('-')
            dct[splits][col] = r[k]

        opdct.append(dct)

    return opdct

# Enter root path
root_path = "./"

if args["mode"] == "create_metadata":
    """
    Create required files for metadata saving and prepares annotation related directories
    """
    # Determine file metadata
    location, paper_name_with_extension = os.path.split(args["paper_path"])
    paper_name_without_extension = paper_name_with_extension.split(".")[0]

    if args["annotator_name"] is None:
        annotator = input("Enter name of annotator: ")

    if not os.path.exists(os.path.join(root_path, "datastore", "metadata.json")):
        os.makedirs(os.path.join(root_path, "datastore"), exist_ok=True)
        file_path = os.path.join(root_path, "datastore", "metadata.json")

        # Create new entry
        paper_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
        annotator=args["annotator_name"]
        metadata_entry = {
            'file_name':paper_name_with_extension,
            'num_questions':None,
            'annotator':annotator
            }
        with open(file_path, "w") as file:
            json.dump({paper_id: metadata_entry}, file, indent=4)
    else:
        # Open existing json file
        with open(os.path.join(root_path, "datastore", "metadata.json"), "r") as file:
            existing_metadata_entries = json.load(file)

        # Create new entry
        paper_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
        annotator=args["annotator_name"]
        metadata_entry = {
            'file_name':paper_name_with_extension,
            'num_questions':None,
            'annotator':annotator
        }
        existing_metadata_entries[paper_id] = metadata_entry
        with open(os.path.join(root_path, "datastore", "metadata.json"),'w') as f:
            json.dump(existing_metadata_entries,f, indent=4)

    # Create the sub-directory of the paper being handled
    os.makedirs(os.path.join(root_path, "datastore", paper_name_without_extension), exist_ok=True)

    # Create the screenshots directory for each paper
    os.makedirs(os.path.join(root_path, "datastore", paper_name_without_extension, "screenshots"), 
                exist_ok=True)
    
    # Copy the paper from the raw_dataset to the sub-directory created
    shutil.copy(args["paper_path"], os.path.join(root_path, "datastore", paper_name_without_extension))

if args["mode"] == "create_annotation":
    """
    Create annotations.csv
    """

    if args["datastore_path"] is not None:
        filtered_directories = [i for i in os.listdir(args["datastore_path"]) if not i.startswith(".")]
        for paper_folders in os.listdir(args["datastore_path"]):
            if not paper_folders in ["metadata.json", ".DS_Store"]:
                paper_path = os.path.join(args["datastore_path"], paper_folders)
                location, paper_name_with_extension = os.path.split(paper_path)
                paper_name_without_extension = paper_name_with_extension.split(".")[0]
                paper_id_determined = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
                annotation_file = create_annotations_helper(paper_path, paper_id_determined)
                annotation_file.to_csv(os.path.join(paper_path,'annotations.csv'), index=False)
    else:
         # Determine file metadata
        location, paper_name_with_extension = os.path.split(args["paper_path"])
        paper_name_without_extension = paper_name_with_extension.split(".")[0]
        paper_id_determined = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
        annotation_file = create_annotations_helper(args["paper_path"], paper_id_determined)
        annotation_file.to_csv(os.path.join(args["paper_path"],'annotations.csv'),index=False)


if args["mode"] == "freeze_annotation":
    """
    Create/appends to root/annotations.jsonl after human annotations.
    """

    if args["datastore_path"] is not None:
        filtered_directories = [i for i in os.listdir(args["datastore_path"]) if not i.startswith(".")]
        for paper_folders in os.listdir(args["datastore_path"]):
            if not paper_folders in ["metadata.json", ".DS_Store"]:
                paper_path = os.path.join(args["datastore_path"], paper_folders)
                anfile = pd.read_csv(os.path.join(paper_path,'annotations.csv'))
                all_anns = get_dict_array(anfile)
                with jsonlines.open(os.path.join(root_path, "datastore",'annotation.jsonl'), mode='a') as writer:
                    for ann in all_anns:
                        writer.write(ann)
                writer.close()

                
    else:
        print('error: datastore path not specified!')
