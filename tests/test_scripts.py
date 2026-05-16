import os


def test_poetry_script():
    assert os.path.isfile(os.path.join("check_poetry_version.sh")), (
        "check_poetry_version.sh not found in the root directory"
    )
