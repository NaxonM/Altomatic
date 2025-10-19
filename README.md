# Altomatic

An AI-powered desktop utility to batch-generate descriptive filenames and alt text for images.

Altomatic streamlines making digital images accessible and SEO-friendly. It leverages multimodal LLMs to analyze image content and automatically generate:

- **SEO-friendly, slug-style filenames** (e.g., `golden-retriever-playing-in-a-park.jpg`)
- **WAI-compliant alternative (alt) text** suitable for screen readers

Built with Python, Altomatic provides an intuitive graphical interface for batch processing, customization, and real-time monitoring.

## Quick Start

The easiest way to get started is to download the latest build from the [**Releases**](https://github.com/NaxonM/Altomatic/releases) page.

Once downloaded, run the application by double-clicking the `launch.bat` script. This batch file automatically sets up a virtual environment and installs all necessary dependencies.

## Key Features

| Feature | Description |
| :--- | :--- |
| 🧠 **AI-Powered Vision** | Utilizes powerful multimodal LLMs for deep image content analysis. |
| 🏷 **Filename Generation** | Creates clean, lowercase, hyphen-separated filenames ideal for SEO and file management. |
| ♿ **Alt Text Generation** | Produces descriptive, context-aware alt text compliant with accessibility standards. |
| 🖼️ **OCR Integration** | Optionally uses Tesseract OCR to extract and incorporate text from images into the analysis prompt. |
| 📂 **Recursive Search** | Process images in the selected folder and all its subdirectories. |
| ✨ **Interactive Results** | Review, copy, and preview generated content in an interactive table after processing. |
|  HEIC/HEIF Support | Process `.heic` and `.heif` images seamlessly. |
| 🔠 **Granular Control** | Customize the level of detail for generated text (Minimal, Normal, Detailed). |
| 🌍 **Multilingual Output** | Generate filenames and alt text in multiple languages, including English and Persian. |
| 🖥️ **Modern UI** | Features an intuitive drag-and-drop interface for processing individual files or entire folders. |
| 🎨 **Customizable Themes** | Includes multiple themes to suit user preference. |
| 🧾 **Usage Monitoring** | Tracks API token consumption per session and provides a real-time activity log. |
| 🔧 **Persistent Settings** | All user preferences, including API key and theme selection, are saved locally across sessions. |
| 🌐 **Provider Choice** | Supports both OpenAI and OpenRouter, allowing access to a diverse range of models. |
| 🕵️ **Proxy Detection** | Automatically detects system proxy settings for seamless operation in corporate environments. |
| 📝 **Prompt Editing** | Customize the prompt templates used for generating filenames and alt text. |
| 🧠 **Request Context** | Provide additional context for each image analysis to guide the AI's response. |

## Prerequisites

- **Python 3.11+**
- **API Key**: An active API key from **OpenAI** or **OpenRouter** with access to a vision model.
- **(Optional) Tesseract OCR**: For text extraction from images, Tesseract must be installed separately.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NaxonM/Altomatic.git
   cd Altomatic
   ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Install Tesseract OCR:**
   Download and install Tesseract from the [official repository](https://github.com/UB-Mannheim/tesseract/wiki). After installation, you must configure the path to the Tesseract executable within the application's **Advanced -> Automation** tab.

## Configuration

### API Key Setup

Altomatic supports both OpenAI and OpenRouter. You will need an API key for the provider you wish to use.

1. Launch the application.
2. Navigate to the **Prompts & Model -> LLM Provider** tab.
3. Select your desired provider (OpenAI or OpenRouter).
4. Enter your API key in the corresponding field. You can obtain a key from [OpenAI](https://platform.openai.com/api-keys) or [OpenRouter](https://openrouter.ai/keys).

Your API keys are stored locally in an obfuscated format and are only used for direct communication with the respective API.

### Proxy Configuration

Altomatic automatically detects and uses your system's proxy settings. If you need to override these settings, you can do so in the **Advanced -> Network** tab by providing a custom proxy URL.

## Usage

To run the application from the source code, execute the following command in the project's root directory:
```bash
python -m src.altomatic
```
Alternatively, pre-built executables are available for download from the [**Releases**](https://github.com/NaxonM/Altomatic/releases) page.

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

## Author

- **Mehdi Bazyar** - [GitHub Profile](https://github.com/NaxonM)
