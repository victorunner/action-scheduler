from pathlib import Path

import yaml


def read_yaml_file_to_dict(
    yaml_file_path: Path | str, encoding: str | None = 'utf-8'
) -> dict:
    # encoding = None => platform-dependent encoding (locale.getencoding() is called
    # to get the current locale encoding)
    return yaml.safe_load(Path(yaml_file_path).read_text(encoding=encoding))
