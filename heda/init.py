from pathlib import Path
from heda.config import get_username
from heda.utils.git_utils import git_add_commit, git_init
from heda.templates.experiment_yaml import experiment_yaml_template
from heda.templates.sample_code import sample_code_template

def create_directory_structure(base_path: Path) -> None:
    
    (base_path / "src").mkdir(parents=True)
    (base_path / "data").mkdir()
    (base_path / "outputs").mkdir()
    (base_path / ".heda").mkdir()

def create_template_files(base_path: Path, exp_name: object) -> None:
    
    (base_path / "requirements.txt").write_text("# Add dependencies here\n")
    experiment_yaml = experiment_yaml_template.format(exp_name=exp_name)
    (base_path / "experiment.yaml").write_text(experiment_yaml)
    (base_path / "src" / "main.py").write_text(sample_code_template)
