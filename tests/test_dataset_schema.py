import json, jsonschema, pathlib

def test_schema_loads():
    schema = json.load(open("benchmark/datasets/phase2_mismatch_labels.schema.json"))
    jsonschema.Draft202012Validator.check_schema(schema)

def test_example_rows_validate():
    import jsonschema
    schema = json.load(open("benchmark/datasets/phase2_mismatch_labels.schema.json"))
    validator = jsonschema.Draft202012Validator(schema)
    path = pathlib.Path("benchmark/datasets/phase2_mismatch_labels.jsonl")
    assert path.exists()
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        obj = json.loads(line)
        validator.validate(obj)
