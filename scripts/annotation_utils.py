import os
import re
import cv2
import uuid
import json
import argparse
import glob
import shutil
import jsonlines
import numpy as np
import pandas as pd
from tqdm import tqdm
from collections import Counter

"""
This script contains the set of utility functions
useful for the annotator
"""

parser = argparse.ArgumentParser(description='Prepare uniform directory structure')
parser.add_argument('-m', '--mode', help='The annotations utility mode', required=False)
parser.add_argument('-pp', '--paper_path', help='The name of paper', required=False)
parser.add_argument('-dp', '--datastore_path', help='The path of datastore', required=False)
parser.add_argument('-an', '--annotator_name', help='The name of annotator', required=False)
parser.add_argument('-u', '--update', help='Update an entry', required=False, default=False)
parser.add_argument('--overwrite', dest='overwrite', action='store_true', help='overwrite existing annotations.csv?',
                    required=False, default=False)
args = vars(parser.parse_args())


def create_annotations_helper(paper_path, paper_id):
    """
    This method is the helper method to create annotations.csv
    :param paper_path: Path to the paper folder
    :param paper_id: UUID of the paper
    :return: Returns the basic empty annotation dataframe with pre-filled columns
    """
    questions_directory = 'screenshots'
    context_directory = 'screenshots'

    # Extract all screenshots into respective lists
    files = [os.path.basename(file_name) for file_name in
             glob.glob(os.path.join(paper_path, questions_directory, '*.png'))]
    questions = pd.Series([file_name.split('_')[0] for file_name in files if file_name[0] == 'q']).unique()

    # Fields for automatic annotation
    sample_ids = questions
    paper_ids = [paper_id] * len(questions)
    image_list = []
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
        image_list_for_question = glob.glob(os.path.join(paper_path, questions_directory, f'{question}_*.png'))

        # in case a single question is split into multiple screenshots
        image_list.append([os.path.basename(image_path) for image_path in image_list_for_question])

        image_example = image_list[-1][-1]

        # if context exists for the example question
        if 'c' in image_example:

            # context num
            cfile = image_example.split('_')[-1]
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
    annotation_file_internal = pd.DataFrame(
        data={
            "paper_id-input": paper_ids,
            "sample_id-input": sample_ids,
            "page_number-input": page_number,
            "input_image_location-input": image_list,
            "section_instruction-input": instruction,
            "context-input": context_list,
            "input_text_parsed-input": input_text_parsed,
            "explanation-output": explanation,
            "final_answer-output": final_answer,
            "final_answer_range-output": final_answer_range,
            "category-input": category
        }
    )
    return annotation_file_internal


def get_dict_array(annotation_dataframe):
    """
    This method returns a dictionary array from the annotation dataframe
    :param annotation_dataframe: The annotation.csv loaded as a dataframe
    :return: Returns the array of output dictionaries
    """
    ann_df = annotation_dataframe.astype(str)
    output_dict_array = []

    for idx, row in ann_df.iterrows():
        output_dict = {'input': {}, 'output': {}}
        for column in list(ann_df.columns):
            field_name, input_or_output_identifier = column.split('-')
            output_dict[input_or_output_identifier][field_name] = row[column]
        output_dict_array.append(output_dict)

    return output_dict_array


def merge_images(image_list):
    """
    Given a list of image array, merge them into a single image with a padding
    :param image_list: Numpy array of images in a list
    :return: The merged image array
    """
    # Find the maximum width among all images
    max_width = max(image.shape[1] for image in image_list)

    # Pad images to have the same width
    padded_images_list = []
    for image in image_list:
        height, width, _ = image.shape
        pad_width = max_width - width
        padded_image = np.pad(image, ((0, 0), (0, pad_width), (0, 0)), constant_values=255)
        padded_images_list.append(padded_image)
    return np.concatenate(padded_images_list, axis=0)


def merge_split_screenshots(paper_path):
    """
    This method merges screenshots that are in multiple parts using OpenCV.
    Specifically files of the following format: q<number>_<blob>_c<number>.png
    :param paper_path: Folder path of the paper
    :return: Void
    """
    screenshots_folder_path = os.path.join(paper_path, "screenshots")

    # Determine context images that have splits
    contexts_list = [i for i in os.listdir(screenshots_folder_path) if i.startswith('c')]
    only_context_list = [i.split('_')[0] for i in os.listdir(screenshots_folder_path) if i.startswith('c')]
    contexts_with_splits_list = [context for context, count in Counter(only_context_list).items() if count > 1]
    context_images_to_be_merged = []
    for context_with_split in contexts_with_splits_list:
        contexts_to_be_merged = []
        for context_image in contexts_list:
            if context_with_split in context_image:
                contexts_to_be_merged.append(os.path.join(screenshots_folder_path, context_image))
        context_images_to_be_merged.append(sorted(contexts_to_be_merged))

    # Determine question images that have splits
    questions_list = [i for i in os.listdir(screenshots_folder_path) if i.startswith('q')]
    questions_without_context_list = [i.split('_')[0] for i in os.listdir(screenshots_folder_path) if i.startswith('q')]
    questions_with_splits_list = [question for question, count in Counter(questions_without_context_list).items() if
                                  count > 1]
    question_images_to_be_merged = []
    for question_with_split in questions_with_splits_list:
        questions_to_be_merged = []
        for question_image in questions_list:
            if question_with_split in question_image:
                questions_to_be_merged.append(os.path.join(screenshots_folder_path, question_image))
        question_images_to_be_merged.append(sorted(questions_to_be_merged))

    images_to_be_merged = context_images_to_be_merged + question_images_to_be_merged

    for image_group_to_be_merged in images_to_be_merged:
        image_list = []
        merged_image_name = os.path.basename(re.sub(r'_\d+', '', image_group_to_be_merged[0]))
        for child_image_path in image_group_to_be_merged:
            img = cv2.imread(child_image_path)
            image_list.append(img)

            # Track images with split with markers
            os.rename(child_image_path,
                      os.path.join(
                          os.path.dirname(child_image_path),
                          "CORRECTED_" + os.path.basename(child_image_path))
                      )

        # Write out merged file
        merged_image = merge_images(image_list)
        cv2.imwrite(os.path.join(screenshots_folder_path, merged_image_name), merged_image)
    print(f"\033[92mMERGE STATUS of {paper_path}: OK", '\u2713\033[0m')


if __name__ == "__main__":

    # Enter a root path
    root_path = "./"

    if args["mode"] == "create_metadata":
        """
        Create required files for metadata saving and prepares annotation related directories
        """
        if args["paper_path"] is None:
            raise ValueError("Required --paper_path value not specified!")

        # Determine file metadata
        location, paper_name_with_extension = os.path.split(args["paper_path"])
        paper_name_without_extension = paper_name_with_extension.split(".")[0]

        if args["annotator_name"] is None:
            annotator = input("Enter name of annotator: ")
        else:
            annotator = args["annotator_name"]

        if args["datastore_path"] is None:
            raise ValueError("Required --datastore_path value not specified!")

        if not os.path.exists(os.path.join(args["datastore_path"], "metadata.json")):
            os.makedirs(args["datastore_path"], exist_ok=True)
            file_path = os.path.join(args["datastore_path"], "metadata.json")

            # Create new entry
            paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
            metadata_entry = {
                'file_name': paper_name_with_extension,
                'num_questions': None,
                'annotator': annotator
            }
            with open(file_path, "w") as file:
                json.dump({paper_id: metadata_entry}, file, indent=4)
        else:
            # Open existing json file
            with open(os.path.join(args["datastore_path"], "metadata.json"), "r") as file:
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
            with open(os.path.join(args["datastore_path"], "metadata.json"), 'w') as f:
                json.dump(existing_metadata_entries, f, indent=4)

        # Create the subdirectory of the paper being handled
        os.makedirs(os.path.join(args["datastore_path"], paper_name_without_extension), exist_ok=True)

        # Create the screenshots directory for each paper
        os.makedirs(os.path.join(args["datastore_path"], paper_name_without_extension, "screenshots"),
                    exist_ok=True)

        # Copy the paper from the raw_dataset to the subdirectory created
        shutil.copy(args["paper_path"], os.path.join(args["datastore_path"], str(paper_name_without_extension)))
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

                    try:
                        annotation_file = create_annotations_helper(paper_path, paper_id_determined)
                        # sorting by question number
                        annotation_file['sort_col'] = annotation_file['sample_id-input'].apply(
                            lambda x: int(x.split('q')[-1]))
                        annotation_file = annotation_file.sort_values(by=['sort_col'])
                        annotation_file = annotation_file.drop(columns=['sort_col'])

                        # saving.
                        if annotation_file.shape[0] == 0:
                            print(f'No screenshots found for {os.path.basename(paper_path)} - skipping')
                            continue
                        annotation_file.to_csv(os.path.join(paper_path, 'annotations.csv'), index=False)
                    except Exception as e:
                        print(f'Error in {paper_path}!\nError: {str(e)}')
        else:
            if args["paper_path"] is None:
                raise ValueError("One of --paper_path or --datastore_path value is required!")

            # Determine file metadata
            location, paper_name_with_extension = os.path.split(args["paper_path"])
            paper_name_without_extension = paper_name_with_extension.split(".")[0]
            paper_id_determined = str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_name_without_extension))
            annotation_file = create_annotations_helper(args["paper_path"], paper_id_determined)

            # Overwrite functionality for single file mode
            if not args['overwrite'] and os.path.exists(os.path.join(args["paper_path"], 'annotations.csv')):
                print(
                    f'{os.path.join(args["paper_path"], "annotations.csv")} exists ; re-run command with '
                    f'"--overwrite" flag to overwrite.')

            # sorting by question number
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

        if args["datastore_path"] is None:
            raise ValueError("Required --datastore_path value not specified!")
        else:
            filtered_directories = [i for i in os.listdir(args["datastore_path"]) if not i.startswith(".")]
            for paper_folders in os.listdir(args["datastore_path"]):
                if paper_folders not in ["metadata.json", ".DS_Store"]:
                    paper_path = os.path.join(args["datastore_path"], paper_folders)
                    annotation_dataframe = pd.read_csv(os.path.join(paper_path, 'annotations.csv'))
                    all_annotations = get_dict_array(annotation_dataframe)
                    with jsonlines.open(os.path.join(args["datastore_path"], 'annotation.jsonl'), mode='a') as writer:
                        for annotation in all_annotations:
                            writer.write(annotation)
                    writer.close()

    if args["mode"] == "merge_screenshots":
        """
        Merge screenshots of contexts and questions
        """
        if args["datastore_path"] is not None:
            filtered_directories = [i for i in os.listdir(args["datastore_path"]) if not i.startswith(".")]
            for paper_folders in filtered_directories:
                paper_path = os.path.join(args["datastore_path"], paper_folders)
                merge_split_screenshots(paper_path)
        else:
            if args["paper_path"] is None:
                raise ValueError("One of --paper_path or --datastore_path value is required!")
            merge_split_screenshots(args["paper_path"])



