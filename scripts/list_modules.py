
import os
import ast
import json

def find_ui_classes(directory):
    """
    Parses Python files in a directory to find classes that inherit from UI-related base classes.
    """
    ui_classes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=filepath)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                is_ui_class = False
                                for base in node.bases:
                                    # Handle tk.Frame, ttk.Frame, etc.
                                    if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                                        if base.value.id in ['tk', 'ttk']:
                                            is_ui_class = True
                                            break
                                    # Handle Frame, Toplevel, etc. when imported directly
                                    if isinstance(base, ast.Name):
                                        if base.id in ['Frame', 'Toplevel', 'Dialog', 'Window']:
                                            is_ui_class = True
                                            break

                                if is_ui_class or node.name.endswith('View'):
                                    module_path = os.path.relpath(filepath, 'src/').replace(os.sep, '.')[:-3]
                                    if module_path not in ui_classes:
                                        ui_classes[module_path] = []

                                    dependencies = []
                                    for b in node.bases:
                                        if isinstance(b, ast.Attribute) and isinstance(b.value, ast.Name):
                                            dependencies.append(f"{b.value.id}.{b.attr}")
                                        elif isinstance(b, ast.Name):
                                            dependencies.append(b.id)

                                    ui_classes[module_path].append({
                                        'class_name': node.name,
                                        'dependencies': dependencies
                                    })
                    except Exception as e:
                        print(f"Error parsing {filepath}: {e}")
    return ui_classes

if __name__ == "__main__":
    ui_dir = 'src/altomatic/ui'
    output_dir = 'docs/migration'
    output_file = os.path.join(output_dir, 'current_ui.json')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    inventory = find_ui_classes(ui_dir)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=4)

    print(f"UI class inventory saved to {output_file}")
