#!/bin/bash

my_fn=tt_bench.txt
cp_fn=imsrgp_bench.txt

echo "--- BENCHMARK FOR testing_tensorflow_v2 ---" |& tee $my_fn
echo "--- BENCHMARK FOR imsrg_pairing ---" |& tee $cp_fn

for i in 2 4 6 8 10
do
    echo "Executing TF on n_holes=$i ---------------------------" |& tee -a $my_fn
#    python -m timeit "from testing_tensorflow_v2_bench import run; run($i)" |& tee -a $my_fn
    kernprof -l testing_tensorflow_v2_bench.py $i |& tee -a $my_fn
    python -m line_profiler testing_tensorflow_v2_bench.py.lprof &>> $my_fn
    echo "line profile complete"
    python -m memory_profiler testing_tensorflow_v2_bench.py $i &>> $my_fn
    echo "memory profile complete"
    echo "---------------------------------------------\n" |& tee -a $my_fn
    echo "" |& tee -a $my_fn    


    echo "Executing NP on n_holes=$i ---------------------------" |& tee -a $cp_fn
#    python -m timeit "from imsrg_pairing_bench import main; main($i)" |& tee -a $cp_fn
    kernprof -l imsrg_pairing_bench.py $i |& tee -a $cp_fn
    python -m line_profiler imsrg_pairing_bench.py.lprof &>> $cp_fn
    echo "line profile complete"
    python -m memory_profiler imsrg_pairing_bench.py $i &>> $cp_fn
    echo "memory profile complete"
    echo "---------------------------------------------" |& tee -a $cp_fn
    echo "" |& tee -a $cp_fn    
done

