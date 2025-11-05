$env:PORT_GRADER = '8002'
$env:PORT_SCORER = '9001'
$env:REPEAT = '30'
pytest -q tests/test_post_deterministic.py -s
