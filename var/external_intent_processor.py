import argparse
import json
import os
import sys
import time

from lib.config_handler import load_config_file
from lib.intent_handler import process_intent
from lib.logging_handler import CustomLogger

##############
# Setup App
##############
app_name = "external_intent_processor"
__version__ = "1.0"
start_time = time.time()
vector_playground_url = ''

def get_arguments():
    # Set up argument parser with description and help text
    parser = argparse.ArgumentParser(
        description='Vector Internal Intent Processor. Processes user queries for a specific bot and language.'
    )
    parser.add_argument(
        'bot_serial',
        help='Bot serial number (required)',
        type=str
    )
    parser.add_argument(
        'locale',
        help='Locale identifier (required, e.g., "en_US", "fr_FR")',
        type=str
    )
    parser.add_argument(
        'user_query',
        help='User query to be processed (required)',
        type=str
    )

    # Error handling if arguments are missing
    if len(sys.argv) < 4:
        parser.print_help()
        sys.exit(1)

    # Parse arguments
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"Error: {e}")
        parser.print_help()
        sys.exit(1)

    return args


def intent_request(args):
    url = f"{vector_playground_url}/{args.bot_serial}/{args.locale}/{args.user_query}"



def main():
    # Get passed arguments
    args = get_arguments()

    intents = load_intents()

    logger.info(args)
    logger.debug(intents)

    intent_result = process_intent(intents, args.bot_serial, args.locale, args.user_query)

    logger.info(f"Took {time.time() - start_time} seconds")

if __name__ == '__main__':
    main()