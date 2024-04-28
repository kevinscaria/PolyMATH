# PolyMATH
## Steps for benchmark creation.
Step 0: collect screenshots, rename 

Step 1:
Prepare script: creates 
- metadata json (updates if it already exists) in the individual folder
- annotation csv within the individual folder. Populates all the fields it can

Step 2:
Manual annotation

Step 3:
Run a script that converts 
- annotation csv to json with the index and subindex structure we decided. Annotation json gets saved to global folder.
- all individual metadata json into a single global one?
  
Step 4:
Git merge to combined annotation and metadata json in the global folder.

