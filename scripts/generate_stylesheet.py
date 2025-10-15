
import os
import sys
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.resources import design_tokens

def generate_stylesheet():
    """
    Reads the base.qss file, replaces the design token placeholders,
    and saves the generated stylesheet.
    """
    qss_template_path = 'src/app/resources/styles/base.qss'
    generated_qss_path = 'src/app/resources/styles/generated.qss'

    with open(qss_template_path, 'r', encoding='utf-8') as f:
        qss_template = f.read()

    # Find all placeholders like {{Colors.PRIMARY}}
    placeholders = re.findall(r'\{\{(.*?)\}\}', qss_template)

    processed_qss = qss_template
    for placeholder in placeholders:
        try:
            # Split 'Colors.PRIMARY' into class and attribute
            class_name, attr_name = placeholder.strip().split('.')
            # Get the class from design_tokens module
            token_class = getattr(design_tokens, class_name)
            # Get the value of the attribute
            value = getattr(token_class, attr_name)
            # Replace the placeholder
            processed_qss = processed_qss.replace(f'{{{{{placeholder}}}}}', value)
        except (AttributeError, ValueError) as e:
            print(f"Warning: Could not resolve placeholder '{{{placeholder}}}': {e}")

    with open(generated_qss_path, 'w', encoding='utf-8') as f:
        f.write(processed_qss)

    print(f"Stylesheet generated at {generated_qss_path}")

if __name__ == "__main__":
    generate_stylesheet()
