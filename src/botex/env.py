import os
import logging
logger = logging.getLogger("botex")

from dotenv import load_dotenv, dotenv_values

def load_botex_env(env_file = "botex.env") -> dict:
    """
    Load botex environment variables from a file and return them as a dict.
    Also loads them into the environment using load_dotenv.

    Args:
        env_file (str, optional): The path to the .env file containing
            the botex configuration. Defaults to "botex.env".

    Returns:
        dict: A dictionary containing the loaded environment variables.
              Returns an empty dict if the file doesn't exist.
    """
    if not os.path.exists(env_file):
        logger.warning(
            f"Could not read any botex environment variables from '{env_file}' "
            "as the file does not exist. "
            "Please make sure that the file is in the right location and that "
            "it sets the botex environment variables that you need."
        )
        return {}

    # Load into environment for other parts of the code that might use os.getenv
    load_dotenv(env_file)

    # Load values into a dictionary to return
    env_vars = dotenv_values(env_file)

    if env_vars:
        logger.info(f"Loaded botex environment variables from '{env_file}'")
    else:
        logger.info(
            f"botex environment variables parsed from '{env_file}'. "
            "No new environment variables were set (or file was empty)."
        )
    return env_vars
