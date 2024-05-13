import os
import uuid
import json
import argparse
import glob
import shutil
import jsonlines
import pandas as pd
from tqdm import tqdm

"""
This script contains the set of utility functions
useful for the annotator
"""

parser = argparse.ArgumentParser(description='Prepare uniform directory structure')
parser.add_argument('-m', '--mode', help='The annotations utility mode', required=False)
parser.add_argument('-pp', '--paper_path', help='The name of paper', required=False)
parser.add_argument('-dp', '--datastore_path', help='The path of datastore', required=True)
parser.add_argument('-an', '--annotator_name', help='The name of annotator', required=False)
parser.add_argument('-u', '--update', help='Update an entry', required=False, default=False)
parser.add_argument('--overwrite', dest='overwrite', action='store_true', help='overwrite existing annotations.csv?',
                    required=False, default=False)
args = vars(parser.parse_args())


def create_annotations_helper(paper_path, paper_id):
    questions_directory = 'screenshots'
    context_directory = 'screenshots'

    # Extract all screenshots into respective lists
    files = [os.path.basename(file_name) for file_name in
             glob.glob(os.path.join(paper_path, questions_directory, '*.png'))]
    questions = pd.Series([file_name.split('_')[0] for file_name in files if file_name[0] == 'q']).unique()

    # Fields for automatic annotation
    sample_ids = questions
    paper_ids = [paper_id] * len(questions)
    img_list = []
    context_list = []
    input_text_parsed = []

    # Fields for manual annotation
    instruction = []
    explanation = []
    final_answer = []
    final_answer_range = []
    page_number = []
    category = []

    for idx, question in tqdm(enumerate(questions), total=len(questions)):

        # list of all images for this question
        img_list_for_question = glob.glob(os.path.join(paper_path, questions_directory, f'{question}_*.png'))

        # in case a single question is split into multiple screenshots
        img_list.append([os.path.basename(img_path) for img_path in img_list_for_question])

        img_example = img_list[-1][-1]

        # if context exists for the example question
        if 'c' in img_example:

            # context num
            cfile = img_example.split('_')[-1]
            context_files = [os.path.basename(p) for p in
                             glob.glob(os.path.join(paper_path, questions_directory, f'{cfile}'))]

            # matches c<num>_*.png, so all parts of c<num> included
            cfile = cfile.replace('.png', '_*.png')
            context_files += [os.path.basename(p) for p in
                              glob.glob(os.path.join(paper_path, context_directory, f'{cfile}'))]

            # if context files not found
            if not len(context_files):
                print('context not found!')
                context_list.append("NOT_FOUND_ERROR")
            else:
                context_list.append(", ".join(context_files))
        else:
            context_list.append("NO_CONTEXT")

        input_text_parsed.append('')
        instruction.append('')
        final_answer.append('')
        final_answer_range.append('')
        page_number.append('')
        explanation.append('')
        category.append('')

    # Create schema for annotation table
    annotation_file = pd.DataFrame(
        data={
            "paper_id-input": paper_ids,
            "sample_id-input": sample_ids,
            "page_number-input": page_number,
            "input_image_location-input": img_list,
            "section_instruction-input": instruction,
            "context-input": context_list,
            "input_text_parsed-input": input_text_parsed,
            "explanation-output": explanation,
            "final_answer-output": final_answer,
            "final_answer_range-output": final_answer_range,
            "category-input": category
        }
    )
    return annotation_file


def get_dict_array(annotation_dataframe):
    # getting nested-index JSON from annotation csv
    ann_df = annotation_dataframe.astype(str)
    output_dict_array = []

    for idx, row in ann_df.iterrows():
        output_dict = {'input': {}, 'output': {}}
        for column in list(ann_df.columns):
            field_name, input_or_output_identifier = column.split('-')
            output_dict[input_or_output_identifier][field_name] = row[column]
        output_dict_array.append(output_dict)

    return output_dict_array


# Driver code starts here
root_path = "../"

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
        paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
        annotator = args["annotator_name"]
        metadata_entry = {
            'file_name': paper_name_with_extension,
            'num_questions': None,
            'annotator': annotator
        }
        with open(file_path, "w") as file:
            json.dump({paper_id: metadata_entry}, file, indent=4)
    else:
        # Open existing json file
        with open(os.path.join(root_path, "datastore", "metadata.json"), "r") as file:
            existing_metadata_entries = json.load(file)

        # Create new entry
        paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
        annotator = args["annotator_name"]
        metadata_entry = {
            'file_name': paper_name_with_extension,
            'num_questions': None,
            'annotator': annotator
        }
        existing_metadata_entries[paper_id] = metadata_entry
        with open(os.path.join(root_path, "datastore", "metadata.json"), 'w') as f:
            json.dump(existing_metadata_entries, f, indent=4)

    # Create the subdirectory of the paper being handled
    os.makedirs(os.path.join(root_path, "datastore", paper_name_without_extension), exist_ok=True)

    # Create the screenshots directory for each paper
    os.makedirs(os.path.join(root_path, "datastore", paper_name_without_extension, "screenshots"),
                exist_ok=True)

    # Copy the paper from the raw_dataset to the subdirectory created
    shutil.copy(args["paper_path"], os.path.join(root_path, "datastore", paper_name_without_extension))
    print(f'Created directory for {os.path.join(root_path, "datastore", paper_name_without_extension)}')

if args["mode"] == "create_annotation":
    """
    Create annotations.csv after you take screenshots
    """

    if args["datastore_path"] is not None:
        filtered_directories = [i for i in os.listdir(args["datastore_path"]) if not i.startswith(".")]
        for paper_folder in os.listdir(args["datastore_path"]):
            paper_path = os.path.join(args["datastore_path"], paper_folder)

            # Allow bulk annotation generation for files that was not run previously.
            # Potentially destructive operation.
            # Advise caution before making changes to this line
            if os.path.exists(os.path.join(paper_path, "annotations.csv")):
                continue

            if paper_folder not in ["metadata.json", ".DS_Store"]:
                location, paper_name_with_extension = os.path.split(paper_path)
                paper_name_without_extension = paper_name_with_extension.split(".")[0]
                paper_id_determined = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
                annotation_file = create_annotations_helper(paper_path, paper_id_determined)

                # sorting by q number
                annotation_file['sort_col'] = annotation_file['sample_id-input'].apply(lambda x: int(x.split('q')[-1]))
                annotation_file = annotation_file.sort_values(by=['sort_col'])
                annotation_file = annotation_file.drop(columns=['sort_col'])

                # saving.
                if annotation_file.shape[0] == 0:
                    print(f'No screenshots found for {os.path.basename(paper_path)} - skipping')
                    continue
                annotation_file.to_csv(os.path.join(paper_path, 'annotations.csv'), index=False)
    else:
        # Determine file metadata
        location, paper_name_with_extension = os.path.split(args["paper_path"])
        paper_name_without_extension = paper_name_with_extension.split(".")[0]
        paper_id_determined = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
        annotation_file = create_annotations_helper(args["paper_path"], paper_id_determined)

        # Overwrite functionality for single file mode
        if not args['overwrite'] and os.path.exists(os.path.join(args["paper_path"], 'annotations.csv')):
            print(
                f'{os.path.join(args["paper_path"], "annotations.csv")} exists ; re-run command with "--overwrite" to '
                f'overwrite.')

        # sorting by q number
        annotation_file['sort_col'] = annotation_file['sample_id-input'].apply(lambda x: int(x.split('q')[-1]))
        annotation_file = annotation_file.sort_values(by=['sort_col'])
        annotation_file = annotation_file.drop(columns=['sort_col'])

        # saving.
        if annotation_file.shape[0] == 0:
            print(f'No screenshots found for {os.path.basename(args["paper_path"])} - skipping')
        else:
            annotation_file.to_csv(os.path.join(args["paper_path"], 'annotations.csv'), index=False)

if args["mode"] == "freeze_annotation":
    """
    Create/appends to root/annotations.jsonl after human annotations.
    """

    if args["datastore_path"] is not None:
        filtered_directories = [i for i in os.listdir(args["datastore_path"]) if not i.startswith(".")]
        for paper_folders in os.listdir(args["datastore_path"]):
            if not paper_folders in ["metadata.json", ".DS_Store"]:
                paper_path = os.path.join(args["datastore_path"], paper_folders)
                anfile = pd.read_csv(os.path.join(paper_path, 'annotations.csv'))
                all_anns = get_dict_array(anfile)
                with jsonlines.open(os.path.join(root_path, "datastore", 'annotation.jsonl'), mode='a') as writer:
                    for ann in all_anns:
                        writer.write(ann)
                writer.close()
    else:
        print('error: datastore path not specified!')
