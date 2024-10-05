import importlib
import json
import logging
import os
import subprocess
import sys

module_logger = logging.getLogger('vector_playground.intent_controller')


class ModuleLoadingError(Exception):
    """Base exception for module loading errors."""
    pass


class ModuleImportError(ModuleLoadingError):
    """Raised when the module cannot be imported or has issues."""
    pass


class RequirementInstallationError(Exception):
    """Raised when there is an error during the requirements installation."""
    pass


class IntentLoader:
    def __init__(self, intents_path='var/intents'):
        self.intents_path = intents_path
        self.user_intents = []
        self.load_all_intents()


    def load_all_intents(self):
        # List all directories in intents_path
        module_logger.info('Loading all intents...')
        for intent_name in os.listdir(self.intents_path):
            module_logger.debug(f'Loading intent {intent_name}')
            intent_dir = os.path.join(self.intents_path, intent_name)
            if os.path.isdir(intent_dir):
                try:
                    self.load_intent(intent_name, intent_dir)
                except Exception as e:
                    module_logger.error(f"Error loading intent '{intent_name}': {e}")

        module_logger.debug(f"Loaded Intents: {"\n".join(intent.get('name') for intent in self.user_intents)}")

    def load_intent(self, intent_name, intent_dir):
        # Load the JSON configuration
        json_path = os.path.join(intent_dir, f"{intent_name}.json")

        try:
            with open(json_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            module_logger.warning(f"Failed Loading Intent '{intent_name}': File not found")
            return None
        except json.decoder.JSONDecodeError:
            module_logger.warning(f"Failed Loading Intent '{intent_name}': Invalid JSON")
            return None
        except Exception as e:
            module_logger.error(f"Error loading intent '{intent_name}': {e}")
            return None

        # Install requirements if requirements.txt exists
        try:
            requirements_path = os.path.join(intent_dir, 'requirements.txt')
            self.install_requirements(requirements_path)
            module_logger.info(f"Requirements satisfied for {intent_name}")
        except Exception as e:
            module_logger.error(f"Error loading intent '{intent_name}': {e}")
            return None

        # Load the main.py module
        try:
            main_py_path = os.path.join(intent_dir, f"{intent_name}.py")
            module = self.load_module(intent_name, main_py_path)
            module_logger.info(f"Loaded Intent '{intent_name}'")
        except FileNotFoundError as e:
            module_logger.error(f"Error loading intent '{intent_name}': File Not Found")
            return None

        except SyntaxError as e:
            module_logger.error(e)
            return None
        except ImportError as e:
            module_logger.error(e)
            return None

        except Exception as e:
            # Catch any other unexpected errors
            module_logger.error(e)
            return None

        # Store the intent's module and configuration
        config["module"] = module
        self.user_intents.append(config)

    def install_requirements(self, requirements_path):
        """
        Install the Python dependencies specified in the requirements file, but only if
        they haven't been installed before (tracked using a marker file).

        :param requirements_path: Path to the requirements.txt file
        :raises FileNotFoundError: If the requirements.txt file is not found
        :raises RuntimeError: If pip is not found in the virtual environment
        :raises RequirementInstallationError: If there's an issue during installation
        """
        # Marker file to track installation
        marker_file = os.path.join(os.path.dirname(requirements_path), '.requirements_installed')

        # Check if the marker file exists, meaning requirements have already been installed
        if os.path.exists(marker_file):
            return

        # Check if requirements.txt exists
        if not os.path.exists(requirements_path):
            return

        # Locate the pip executable inside the virtual environment
        venv_pip = os.path.join(os.path.dirname(sys.executable), 'pip')

        # Check if the pip executable exists
        if not os.path.exists(venv_pip):
            raise RuntimeError(f"pip not found in the virtual environment: {venv_pip}")

        try:
            # Run pip install using the virtual environment's pip
            subprocess.run([venv_pip, 'install', '-r', requirements_path], check=True)

            # Write marker file to indicate installation is done
            with open(marker_file, 'w') as f:
                f.write('Requirements installed.')

        except subprocess.CalledProcessError as e:
            # Capture and raise errors if pip install fails
            raise RequirementInstallationError(f"Failed to install requirements from '{requirements_path}': {e}")

        except OSError as e:
            # Capture other OS-related errors (e.g., permission issues, executable not found)
            raise RequirementInstallationError(f"An OS error occurred while running pip: {e}")

    def load_module(self, intent_name, module_path):
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(intent_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return module

        except FileNotFoundError as e:
            raise FileNotFoundError()

        except SyntaxError as e:
            raise ModuleImportError(f"Syntax error in module '{intent_name}' at {module_path}: {e}")

        except ImportError as e:
            raise ModuleImportError(f"Import error in module '{intent_name}' at {module_path}: {e}")

        except Exception as e:
            # Catch any other unexpected errors
            raise ModuleLoadingError(f"Unexpected Error loading intent module '{intent_name}' from {module_path}: {e}")


class IntentController:
    def __init__(self, robot, intent_loader):
        self.robot = robot
        self.user_intents = intent_loader.user_intents

    def match_intent(self, user_query):
        matched_intent = None
        user_query_lower = user_query.lower()

        sorted_intents = sorted(self.user_intents, key=lambda x: x["priority"])

        for intent in sorted_intents:
            intent_utterances = intent.get("utterances", [])
            if not intent_utterances:
                continue

            # Match user query with any of the intent utterances
            for utterance in intent_utterances:
                if utterance.lower() in user_query_lower:
                    # Simple substring match
                    matched_intent = intent
                    break

                if matched_intent:
                    break  # Exit

        return matched_intent

    def process_intent(self, user_query):
        module_logger.info("Processing Intent")

        matched_intent = self.match_intent(user_query)

        if matched_intent is None:
            module_logger.info(f"No intent matched.")
            module_logger.debug(f"User Query: {user_query}")
            return None

        module_logger.info(f"Matched intent: {matched_intent.get("name")}")
        module_logger.debug(f"User Query: {user_query}")

        result = self.run_user_intent(matched_intent, user_query)
        return result

    def run_user_intent(self, intent_data, user_query):
        module = intent_data['module']

        if hasattr(module, 'main'):
            return module.main(self.robot, user_query)
        else:
            raise AttributeError(f"The intent '{intent_data.get('intent_name')}' does not have a 'main' function.")

