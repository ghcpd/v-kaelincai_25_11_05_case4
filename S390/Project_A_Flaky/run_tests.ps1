$env:PORT_GRADER = '8001'
$env:PORT_SCORER = '9001'
$env:REPEAT = '30'
pytest -q tests/test_pre_flaky.py -s
