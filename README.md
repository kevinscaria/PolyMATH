# PolyMATH
## Steps for benchmark creation.


#### Step 0: 
Run annotation_utils.sh in the "create_metadata" mode. 
- metadata json (updates if it already exists) in the sub-folder for each paper
- creates the directory structure
```
python ./scripts/annotation_utils.py \
--mode create_metadata \
--paper_path "./<PAPER_NAME_WITH_EXTENSION>" \
--annotator_name kscaria \
```

Step 1:
Go to <paper>/screenshots/ and add images. Naming convention:
- q<n>_<part>_\[c<context>\] []:optional
- c<num>

Step 2:
Run annotation_utils.sh in the "create_annotations" mode. 
- annotation csv within the individual folder. Populates all the fields it can

Step 3:
Manual annotation

Step 3:
Run a script that converts 
- annotation csv to json with the index and subindex structure we decided. \[Annotation json gets saved to global folder.\]

Step 4:
rebase to ensure you have latest main status.
push to branch. ensure merging of changes.
Create PR.

