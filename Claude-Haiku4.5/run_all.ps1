# Master script to run the complete flaky behavior experiment
# Runs Project A (flaky), Project B (deterministic), and generates comparison report
# Windows PowerShell version

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$WORKSPACE_DIR = Split-Path -Parent $SCRIPT_DIR

$PROJECT_A_DIR = Join-Path $WORKSPACE_DIR "Project_A_Flaky"
$PROJECT_B_DIR = Join-Path $WORKSPACE_DIR "Project_B_Deterministic"
$SHARED_DIR = Join-Path $WORKSPACE_DIR "shared_artifacts"
$RESULTS_DIR = Join-Path $SHARED_DIR "results"

Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host "Flaky Behavior Detection & Mitigation - Complete Experiment" -ForegroundColor Cyan
Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Workspace: $WORKSPACE_DIR"
Write-Host "Project A (Flaky): $PROJECT_A_DIR"
Write-Host "Project B (Deterministic): $PROJECT_B_DIR"
Write-Host "Shared artifacts: $SHARED_DIR"
Write-Host ""

# Create results directory
if (-not (Test-Path $RESULTS_DIR)) {
    New-Item -ItemType Directory -Path $RESULTS_DIR | Out-Null
}

# Run Project A (Flaky)
Write-Host "=================================================================================" -ForegroundColor Yellow
Write-Host "PHASE 1: Running Project A (Flaky Baseline)" -ForegroundColor Yellow
Write-Host "=================================================================================" -ForegroundColor Yellow
Write-Host ""

Push-Location $PROJECT_A_DIR
try {
    python "$PROJECT_A_DIR\tests\test_pre_flaky.py"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "✓ Project A tests completed" -ForegroundColor Green
Write-Host ""

# Copy results to shared
Copy-Item "$PROJECT_A_DIR\logs\results_pre.json" $RESULTS_DIR -Force
if (Test-Path "$PROJECT_A_DIR\logs\test_pre_flaky.txt") {
    Copy-Item "$PROJECT_A_DIR\logs\test_pre_flaky.txt" $RESULTS_DIR -Force
}

# Run Project B (Deterministic)
Write-Host "=================================================================================" -ForegroundColor Yellow
Write-Host "PHASE 2: Running Project B (Deterministic Fix)" -ForegroundColor Yellow
Write-Host "=================================================================================" -ForegroundColor Yellow
Write-Host ""

Push-Location $PROJECT_B_DIR
try {
    python "$PROJECT_B_DIR\tests\test_post_deterministic.py"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "✓ Project B tests completed" -ForegroundColor Green
Write-Host ""

# Copy results to shared
Copy-Item "$PROJECT_B_DIR\logs\results_post.json" $RESULTS_DIR -Force
if (Test-Path "$PROJECT_B_DIR\logs\test_post_deterministic.txt") {
    Copy-Item "$PROJECT_B_DIR\logs\test_post_deterministic.txt" $RESULTS_DIR -Force
}

# Generate comparison report
Write-Host "=================================================================================" -ForegroundColor Yellow
Write-Host "PHASE 3: Generating Comparison Report" -ForegroundColor Yellow
Write-Host "=================================================================================" -ForegroundColor Yellow
Write-Host ""

Push-Location $SHARED_DIR
try {
    python compare_results.py `
        "$RESULTS_DIR\results_pre.json" `
        "$RESULTS_DIR\results_post.json" `
        "$RESULTS_DIR\compare_report.md"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host "EXPERIMENT COMPLETE" -ForegroundColor Green
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Results saved to: $RESULTS_DIR" -ForegroundColor Green
Write-Host ""
Write-Host "Key artifacts:"
Write-Host "  - results_pre.json: Project A (flaky) detailed results"
Write-Host "  - results_post.json: Project B (deterministic) detailed results"
Write-Host "  - compare_report.md: Full comparison and analysis"
Write-Host "  - test_pre_flaky.txt: Project A execution log"
Write-Host "  - test_post_deterministic.txt: Project B execution log"
Write-Host ""
Write-Host "To view the comparison report:"
Write-Host "  Get-Content $RESULTS_DIR\compare_report.md"
Write-Host ""
