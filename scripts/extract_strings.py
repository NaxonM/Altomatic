
import os
import subprocess

def extract_strings():
    """
    Extracts translatable strings from the source code using Babel.
    """
    babel_cfg = 'babel.cfg'
    output_pot = 'src/app/resources/locales/altomatic.pot'
    source_dir = 'src/app'

    # Ensure the locales directory exists
    os.makedirs(os.path.dirname(output_pot), exist_ok=True)

    command = [
        'pybabel', 'extract',
        '-F', babel_cfg,
        '-o', output_pot,
        source_dir
    ]

    print(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=True)
    print(f"Template file created at {output_pot}")

if __name__ == "__main__":
    extract_strings()
