experiment_yaml = """\
name: {exp_name}
procedure:
  entrypoint: python src/main.py
claims:
  - metric: accuracy
    operator: ">="
    value: 0.8
"""