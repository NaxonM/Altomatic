# Altomatic

An AI-powered desktop utility for automatically generating descriptive filenames and alt text for images.

Altomatic streamlines the process of making digital images accessible and SEO-friendly. It leverages the GPT-4.1-nano vision model to analyze image content and automatically generate:

  * **SEO-friendly, slug-style filenames** (e.g., `golden-retriever-playing-in-a-park.jpg`)
  * **WAI-compliant alternative (alt) text** suitable for screen readers

Built with Python, Altomatic provides an intuitive graphical interface for batch processing, customization, and real-time monitoring.

## Quick Start

The easiest way to get started is to download the latest build from the [Releases](https://github.com/NaxonM/altomatic/releases) page.

Once downloaded, you can run the application by simply double-clicking the `launch.bat` script. This will set up a virtual environment and install all the necessary dependencies for you.

## Key Features

| Feature | Description |
| :--- | :--- |
| 🧠 **AI-Powered Vision** | Utilizes the GPT-5 and OpenRouter models vision model for deep image content analysis. |
| 🏷 **Filename Generation** | Creates clean, lowercase, hyphen-separated filenames ideal for SEO and file management. |
| ♿ **Alt Text Generation** | Produces descriptive, context-aware alt text compliant with accessibility standards. |
| 🖼️ **OCR Integration** | Optionally uses Tesseract OCR to extract and incorporate text from images into the analysis prompt. |
| 🔠 **Granular Control** | Customize the level of detail for generated text (Minimal, Normal, Detailed). |
| 🌍 **Multilingual Output** | Generate filenames and alt text in multiple languages, including English and Persian. |
| 🖥️ **Modern UI** | Features an intuitive drag-and-drop interface for processing individual files or entire folders. |
| 🎨 **Customizable Themes** | Includes multiple themes (Light, Dark, Solarized, etc.) to suit user preference. |
| 🧾 **Usage Monitoring** | Tracks API token consumption per session and provides a real-time activity log. |
| 🔧 **Persistent Settings** | All user preferences, including API key and theme selection, are saved locally across sessions. |
| 🌐 **Provider Choice** | Supports both OpenAI and OpenRouter, allowing access to a diverse range of models. |
| 🕵️ **Proxy Detection** | Automatically detects system proxy settings for seamless operation in corporate environments. |
| 📝 **Prompt Editing** | Customize the prompt templates used for generating filenames and alt text. |
| 🧠 **Request Context** | Provide additional context for each image analysis to guide the AI's response. |

## Prerequisites

  * **Python 3.11+**
  * **OpenAI API Key**: An active OpenAI API key with access to the `GPT-4.1-nano` vision model is required.
  * **(Optional) Tesseract OCR**: For text extraction from images, Tesseract must be installed separately.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/NaxonM/altomatic.git
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

Altomatic supports both OpenAI and OpenRouter. You will need an API key for the provider you wish to use.

1.  Launch the application.
2.  Navigate to the **Settings** tab.
3.  Select your desired provider (OpenAI or OpenRouter).
4.  Enter your API key in the corresponding field. You can obtain a key from [OpenAI](https://platform.openai.com/api-keys) or [OpenRouter](https://openrouter.ai/keys).

Your API keys are stored locally in an obfuscated format and are only used for direct communication with the respective API.

### Proxy Configuration

Altomatic automatically detects and uses your system's proxy settings. If you need to override these settings, you can do so in the **Settings** tab by providing a custom proxy URL.

## Usage

To run the application from the source code, execute the following command in the project's root directory:

```bash
python -m src.altomatic
```

Alternatively, pre-built executables are available for download from the [Releases](https://github.com/NaxonM/altomatic/releases) page.

## Building from Source

To create a standalone executable from the source code, a build script is provided.

1.  Ensure you have the required dependencies installed:
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```
2.  Run the build script:
    ```bash
    python build_installer.py
    ```

The compiled executable will be located in the `dist/` directory.

## Advanced Usage

### Prompt Editing

You can customize the prompts used to generate filenames and alt text by editing the `prompts.json` file. This file is located in the `src/altomatic/data` directory. You can add new prompts or modify existing ones to suit your needs.

### Request Context

You can provide additional context for each image analysis request in the "Context" text box. This can be used to guide the AI's response and improve the quality of the generated filenames and alt text.

## Author

  * **NaxonM** - [GitHub Profile](https://github.com/NaxonM)