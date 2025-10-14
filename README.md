# Altomatic

An AI-powered desktop utility for automatically generating descriptive filenames and alt text for images.

Altomatic streamlines the process of making digital images accessible and SEO-friendly. It leverages the GPT-4.1-nano vision model to analyze image content and automatically generate:

  * **SEO-friendly, slug-style filenames** (e.g., `golden-retriever-playing-in-a-park.jpg`)
  * **WAI-compliant alternative (alt) text** suitable for screen readers

Built with Python, Altomatic provides an intuitive graphical interface for batch processing, customization, and real-time monitoring.

## Key Features

| Feature | Description |
| :--- | :--- |
| 🧠 **AI-Powered Vision** | Utilizes the GPT-4.1-nano vision model for deep image content analysis. |
| 🏷 **Filename Generation** | Creates clean, lowercase, hyphen-separated filenames ideal for SEO and file management. |
| ♿ **Alt Text Generation** | Produces descriptive, context-aware alt text compliant with accessibility standards. |
| 🖼️ **OCR Integration** | Optionally uses Tesseract OCR to extract and incorporate text from images into the analysis prompt. |
| 🔠 **Granular Control** | Customize the level of detail for generated text (Minimal, Normal, Detailed). |
| 🌍 **Multilingual Output** | Generate filenames and alt text in multiple languages, including English and Persian. |
| 🖥️ **Modern UI** | Features an intuitive drag-and-drop interface for processing individual files or entire folders. |
| 🎨 **Customizable Themes** | Includes multiple themes (Light, Dark, Solarized, etc.) to suit user preference. |
| 🧾 **Usage Monitoring** | Tracks API token consumption per session and provides a real-time activity log. |
| 🔧 **Persistent Settings** | All user preferences, including API key and theme selection, are saved locally across sessions. |

## Prerequisites

  * **Python 3.11+**
  * **OpenAI API Key**: An active OpenAI API key with access to the `GPT-4.1-nano` vision model is required.
  * **(Optional) Tesseract OCR**: For text extraction from images, Tesseract must be installed separately.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/MehdiBazyar99/altomatic.git
    cd altomatic
    ```

2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **(Optional) Install Tesseract OCR:**
    Download and install Tesseract from the [official repository](https://github.com/UB-Mannheim/tesseract/wiki). After installation, you must configure the path to the Tesseract executable within the application's **Settings** tab.

## Configuration

### API Key Setup

Altomatic requires an OpenAI API key to function.

1.  Launch the application.
2.  Navigate to the **Settings** tab.
3.  Enter your OpenAI API key in the designated field. You can obtain a key at [platform.openai.com/api-keys](https://platform.openai.com/account/api-keys).

Your API key is stored locally in an obfuscated format and is only used for direct communication with the OpenAI API.

## Usage

To run the application from the source code, execute the following command in the project's root directory:

```bash
python main.py
```

Alternatively, pre-built executables are available for download from the [Releases](https://github.com/MehdiBazyar99/altomatic/releases) page.

## Building from Source

To create a standalone executable from the source code, you can use `pyinstaller`.

1.  Ensure `pyinstaller` is installed (`pip install pyinstaller`).
2.  Run the following command:
    ```bash
    pyinstaller --onefile --windowed --icon=altomatic_icon.ico main.py
    ```

The compiled executable will be located in the `dist/` directory.

## Author

  * **NaxonM** - [GitHub Profile](https://github.com/NaxonM)