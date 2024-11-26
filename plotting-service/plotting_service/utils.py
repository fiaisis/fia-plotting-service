from contextlib import suppress
from http import HTTPStatus
from pathlib import Path

from fastapi import HTTPException


def safe_check_filepath(filepath: Path, base_path: str) -> None:
    """
    Check to ensure the path does contain the base path and that it does not resolve to some other directory
    :param filepath: the filepath to check
    :param base_path: base path to check against
    :return:
    """
    filepath.resolve(strict=True)
    if not filepath.is_relative_to(base_path):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Invalid path being accessed.")


def _safe_find_file_in_dir(dir_path: Path, base_path: str, filename: str) -> Path | None:
    """
    Check that the directory path is safe and then search for filename in that directory and sub directories
    :param dir_path: Path to check is safe and search in side of
    :param base_path: the base directory of the path often just the /ceph dir on runners
    :param filename: filename to find
    :return: Path to the file or None
    """
    # Do a check as we are handling user entered data here
    try:
        safe_check_filepath(filepath=dir_path, base_path=base_path)
    except OSError:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Invalid path being accessed.") from None

    if dir_path.exists():
        found_paths = list(dir_path.rglob(filename))
        if len(found_paths) > 0 and found_paths[0].exists():
            return found_paths[0]

    return None