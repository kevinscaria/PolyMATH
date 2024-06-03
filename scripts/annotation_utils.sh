# Run this script from the root directory as
# bash scripts/annotation_utils.sh


# Metadata creation & initial setup
ANNOTATOR_NAME=muthu
python ./scripts/annotation_utils.py \
--mode create_metadata \
--paper_path "./raw_dataset/13_14_papers/NTSE-Stage-1-2013-Paper-MAT(Rajasthan).pdf" \
--annotator_name "$ANNOTATOR_NAME" \
--datastore_path "./datastore"

### Single paper merge screenshots tool
#python ./scripts/annotation_utils.py \
#--mode merge_screenshots \
#--paper_path "./datastore/QP_Test_BaseCase"

### Bulk merge screenshots tool
#python ./scripts/annotation_utils.py \
#--mode merge_screenshots \
#--datastore_path "./datastore/"

## Entire datastore bulk annotation creation
# python ./scripts/annotation_utils.py \
# --mode create_annotation \
# --datastore_path "./datastore"

## Single paper annotation creation
#python ./scripts/annotation_utils.py \
#--mode create_annotation \
#--paper_path "./datastore/QP_ Punjab NTSE Stage 1 2017-18 (MAT_LANG_SAT)"

## Freeze annotation
#TO BE ADDED
