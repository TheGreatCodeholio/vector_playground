import json
import logging
import configparser
import os

module_logger = logging.getLogger('vector_playground.config_handler')

default_config = {
    "log_level": 1
}

def load_sdk_configuration(file_path):
    """
    load bot sdk configuration
    :param file_path:
    :return: list of dictionaries containing bot sdk configuration
    """

    sdk_config = []
    module_logger.info(f'Loading SDK Configuratiion')
    if not os.path.exists(file_path):
        raise FileNotFoundError("Vector SDK configuration file not found")

    config = configparser.ConfigParser()

    try:
        # Try to read the config file
        config.read(file_path)
    except configparser.ParsingError as e:
        raise ValueError(f"Error parsing Vector SDK configuration file: {e}")

    # If there are no sections, it's not a proper ini file
    if not config.sections():
        raise ValueError("Vector SDK configuration file is empty")

    for section in config.sections():
        bot_data = {key: value for key, value in config.items(section)}
        bot_data["serial"] = section
        sdk_config.append(bot_data)

    return sdk_config



def load_config_file(file_path):
    """
    Loads the configuration file
    Raises exceptions in case of errors.
    """
    # Attempt to load the configuration file
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        module_logger.warning(f'Configuration file {file_path} not found. Creating default.')
        save_config_file(file_path, default_config)
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f'Failed to load default configuration after creating it: {e}')
    except json.JSONDecodeError:
        raise ValueError(f'Configuration file {file_path} is not in valid JSON format.')
    except Exception as e:
        raise RuntimeError(f'Unexpected Exception while loading file {file_path}: {e}')

    return config_data


def save_config_file(file_path, default_data):
    """Creates a configuration file with default data if it doesn't exist."""
    try:
        with open(file_path, "w") as outfile:
            outfile.write(json.dumps(default_data, indent=4))
        return True
    except Exception as e:
        module_logger.error(f'Unexpected Exception Saving file {file_path} - {e}')
        return None
