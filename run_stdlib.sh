round_from=0
round_to=8


folder_path="result_working/stdlib/PBTFactory_stdlib_without_expert_knowledge"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_stdlib.py -v \
                    -o "$folder_path/$i" \
                    --include_test \
                    -p pipeline_PBTFactory_no_expert_knowledge > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/stdlib/PBTFactory_stdlib"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_stdlib.py -v \
                    -o "$folder_path/$i" \
                    --include_test \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done

folder_path="result_working/stdlib/PBTFactory_stdlib_no_test"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_stdlib.py -v \
                    -o "$folder_path/$i" \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done


folder_path="result_working/stdlib/PBTFactory_stdlib_with_class_interface"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_stdlib.py -v \
                    -o "$folder_path/$i" \
                    --include_test \
                    --include_class_structure \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done


folder_path="result_working/stdlib/pbt_baseline_stdlib"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_stdlib.py -v \
                    -o "$folder_path/$i" \
                    --include_test \
                    -p pipeline_pbt_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done


folder_path="result_working/stdlib/unit_test_baseline_stdlib"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_stdlib.py -v \
                    -o "$folder_path/$i" \
                    --include_test \
                    -p pipeline_unit_test_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done
