round_from=0
round_to=0


folder_path="result_working/evalplus/PBTFactory_evalplus"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_evalplus.py -v \
                    -o "$folder_path/$i" \
                    -p pipeline_PBTFactory > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done


folder_path="result_working/evalplus/pbt_baseline_evalplus"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_evalplus.py -v \
                    -o "$folder_path/$i" \
                    -p pipeline_pbt_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done


folder_path="result_working/evalplus/unit_test_baseline_evalplus"
mkdir -p "$folder_path"
for ((i=round_from; i<=round_to; i++)); do
  nohup python3 -u run_evalplus.py -v \
                    -o "$folder_path/$i" \
                    -p pipeline_unit_test_baseline > "$folder_path/$i.log" 2>&1 &
  echo "Process $i PID: $!"
done
