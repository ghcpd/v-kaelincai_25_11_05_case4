# PowerShell script to run the entire experiment
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r Project_A_Flaky\requirements.txt; python -m pip install -r Project_B_Deterministic\requirements.txt
$env:REPEAT_RUNS=30
pushd Project_A_Flaky; pytest -q; popd
pushd Project_B_Deterministic; pytest -q; popd
python compare_results.py
Write-Host "Done; results at results/results_pre.json and results/results_post.json; compare_report.md"