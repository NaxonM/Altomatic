
import os
import subprocess
import argparse

def init_language(lang):
    """
    Initializes a new language for translation.
    """
    pot_file = 'src/app/resources/locales/altomatic.pot'
    locales_dir = 'src/app/resources/locales'

    command = [
        'pybabel', 'init',
        '-i', pot_file,
        '-d', locales_dir,
        '-l', lang
    ]

    print(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=True)
    print(f"Language '{lang}' initialized.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new language for translation.")
    parser.add_argument("lang", help="The language code (e.g., 'en', 'es', 'fr').")
    args = parser.parse_args()
    init_language(args.lang)
