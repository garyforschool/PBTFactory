round_from=0
round_to=0


folder_path="result_working/large_projects/PBTFactory_real_flutils"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/flutils/test_data \
                    --project_src_code real_project_dataset/flutils/flutils \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_flutils_pbt_baseline"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/flutils/test_data \
                    --project_src_code real_project_dataset/flutils/flutils \
                    -p pipeline_pbt_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_flutils_unit_baseline"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/flutils/test_data \
                    --project_src_code real_project_dataset/flutils/flutils \
                    -p pipeline_unit_test_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_requests"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/requests/test_data \
                    --project_src_code real_project_dataset/requests/requests \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_requests_pbt_baseline"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/requests/test_data \
                    --project_src_code real_project_dataset/requests/requests \
                    -p pipeline_pbt_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_requests_unit_baseline"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/requests/test_data \
                    --project_src_code real_project_dataset/requests/requests \
                    -p pipeline_unit_test_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done


folder_path="result_working/large_projects/PBTFactory_real_werkzeug"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/werkzeug/test_data \
                    --project_src_code real_project_dataset/werkzeug/werkzeug \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_werkzeug_pbt_baseline"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/werkzeug/test_data \
                    --project_src_code real_project_dataset/werkzeug/werkzeug \
                    -p pipeline_pbt_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/large_projects/PBTFactory_real_werkzeug_unit_baseline"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_real_project.py -v \
                    -o "$folder_path/$i" \
                    -d real_project_dataset/werkzeug/test_data \
                    --project_src_code real_project_dataset/werkzeug/werkzeug \
                    -p pipeline_unit_test_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done
