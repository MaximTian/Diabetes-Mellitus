#!/bin/bash
set -e

#tensorflow
source ~/env/tensorflow-env/bin/activate
cd classification
python xgb_hp95.py --offline_test 1
python xgb_lp30.py --offline_test 1
cd ../regression
python xgb.py --offline_test 1
python lgdm.py --offline_test 1
python rf.py --offline_test 1
python dart.py --offline_test 1
python gen_submission.py --offline_test 1
python post_process.py --offline_test 1

