import os
import json
import argparse
import shutil

parser = argparse.ArgumentParser(description='Prepare uniform directory structure')
parser.add_argument('-m','--mode', help='The annotations utility mode', required=True)
parser.add_argument('-pp','--paper_path', help='The name of paper', required=True)
parser.add_argument('-an','--annotator_name', help='The name of annotator', required=True)
args = vars(parser.parse_args())

# Enter root path
root_path = "./"

# Determine file name
location, paper_name_with_extension = os.path.split(args["paper_path"])
paper_name_without_extension = paper_name_with_extension.split(".")[0]


if args["mode"] == "prepare":
    # Create/Append a metadata.json
    if not os.path.exists(os.path.join(root_path, "datastore", "metadata.json")):
        os.makedirs(os.path.join(root_path, "datastore"), exist_ok=True)
        file_path = os.path.join(root_path, "datastore", "metadata.json")

        # Create new entry
        paper_id=hash(paper_name_with_extension)
        annotator=args["annotator_name"]
        metadata_entry = [
            {
            'file_name':paper_name_with_extension,
            'paper_id':paper_id,
            'num_questions':None,
            'annotator':annotator
            }
        ]
        with open(file_path, "w") as file:
            json.dump(metadata_entry, file, indent=4)
    else:
        # Open existing json file
        with open(os.path.join(root_path, "datastore", "metadata.json"), "r") as file:
            existing_metadata_entries = json.load(file)

        # Create new entry
        paper_id=hash(paper_name_with_extension)
        annotator=args["annotator_name"]
        metadata_entry = {
            'file_name':paper_name_with_extension,
            'paper_id':paper_id,
            'num_questions':None,
            'annotator':annotator
        }
        existing_metadata_entries.append(metadata_entry)
        with open(os.path.join(root_path, "datastore", "metadata.json"),'w') as f:
            json.dump(existing_metadata_entries,f, indent=4)

    # Create the sub-directory of the paper being handled
    os.makedirs(os.path.join(root_path, "datastore", paper_name_without_extension), exist_ok=True)
    
    # Copy the paper from the raw_dataset to the sub-directory created
    shutil.copy(args["paper_path"], os.path.join(root_path, "datastore", paper_name_without_extension))

# if args["mode"] == "create_anotation":
#     # Create/Append an annotations.csv
#     if not os.path.exists(os.path.join(root_path, "datastore", "annotations.csv")):
#         os.makedirs(os.path.join(root_path, "datastore", "annotations.csv"), exist_ok=True)
#     else:
#         paper_id=hash(paper_name_with_extension)
#         annotator=args["annotator_name"]
#         metadata_entry = {
#             'file_name':args["paper_name"],
#             'paper_id':paper_id,
#             'num_questions':None,
#             'annotator':annotator
#         }
#         with open(os.path.join(root_path, "datastore", "metadata.json"),'w') as f:
#             json.dump(metadata_entry,f)
