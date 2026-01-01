from heda.config import load_config

def get_username() -> str:
    """
    Load the HEDA config and return the username.

    Raises:
        RuntimeError: if the config is empty or username is missing.
    """
    config = load_config()

    if not config:
        raise RuntimeError("HEDA config not found or empty")

    username = config.get("github_username")
    if not username:
        raise RuntimeError("Username not found in HEDA config")

    return username
