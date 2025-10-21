# Altomatic

An AI-powered desktop utility to batch-generate descriptive filenames and alt text for images.

Altomatic streamlines making digital images accessible and SEO-friendly. It leverages multimodal LLMs to analyze image content and automatically generate:

- **SEO-friendly, slug-style filenames** (e.g., `golden-retriever-playing-in-a-park.jpg`)
- **WAI-compliant alternative (alt) text** suitable for screen readers

Built with Python, Altomatic provides an intuitive graphical interface for batch processing, customization, and real-time monitoring.

## Key Features

| Feature | Description |
| :--- | :--- |
| 🧠 **AI-Powered Vision** | Utilizes powerful multimodal LLMs for deep image content analysis. |
| ✨ **Responsive UI** | Features a modern, responsive layout with auto-scrolling collapsible sections for a seamless experience. |
| 📂 **Flexible Input** | Process a single image or an entire folder of images with a simple drag-and-drop interface. |
| 🏷 **Filename Generation** | Creates clean, lowercase, hyphen-separated filenames ideal for SEO and file management. |
| ♿ **Alt Text Generation** | Produces descriptive, context-aware alt text compliant with accessibility standards. |
| 🖼️ **OCR Integration** | Optionally uses Tesseract OCR to extract and incorporate text from images into the analysis prompt. |
| 📂 **Recursive Search** | Process images in the selected folder and all its subdirectories. |
| ✨ **Interactive Results** | Review, copy, and preview generated content in an interactive table after processing. |
|  HEIC/HEIF Support | Process `.heic` and `.heif` images seamlessly. |
| 🔠 **Granular Control** | Customize the level of detail for generated text (Minimal, Normal, Detailed). |
| 🌍 **Multilingual Output** | Generate filenames and alt text in multiple languages, including English and Persian. |
| 🎨 **Customizable Themes** | Includes multiple themes to suit user preference. |
| 🧾 **Usage Monitoring** | Tracks API token consumption per session and provides a real-time activity log. |
| 🔧 **Persistent Settings** | All user preferences, including API key and theme selection, are saved locally across sessions. |
| 🌐 **Provider Choice** | Supports both OpenAI and OpenRouter, allowing access to a diverse range of models. |
| 🕵️ **Proxy Detection** | Automatically detects system proxy settings for seamless operation in corporate environments. |
| 📝 **Prompt Editing** | Customize the prompt templates used for generating filenames and alt text. |
| 🧠 **Request Context** | Provide additional context for each image analysis to guide the AI's response. |

## How it Works

Altomatic's workflow is designed to be simple and efficient:

1.  **Input:** Drag and drop an image or a folder of images onto the application window.
2.  **Configuration:** Use the **Workflow** and **Prompts & Models** tabs to configure the processing options, such as the AI provider, language, and output settings.
3.  **Processing:** Click the **Process Images** button to start the analysis. Altomatic will send each image to the selected AI provider, along with any context you've provided.
4.  **Output:** The application will generate a new filename and alt text for each image. The results are saved in a session-based folder, and you can view them in an interactive table.

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
   Download and install Tesseract from the [official repository](https://github.com/UB-Mannheim/tesseract/wiki). After installation, you must configure the path to the Tesseract executable in the **Workflow -> OCR Settings** section.

## Configuration

### API Key Setup

Altomatic supports both OpenAI and OpenRouter. You will need an API key for the provider you wish to use.

1. Launch the application.
2. Navigate to the **Prompts & Models** tab.
3. In the **AI Provider & Model** section, select your desired provider (OpenAI or OpenRouter).
4. Enter your API key in the corresponding field. You can obtain a key from [OpenAI](https://platform.openai.com/api-keys) or [OpenRouter](https://openrouter.ai/keys).

Your API keys are stored locally in an obfuscated format and are only used for direct communication with the respective API.

### Proxy Configuration

Altomatic automatically detects and uses your system's proxy settings. If you need to override these settings, you can do so by opening the settings dialog and navigating to the **Network** tab to provide a custom proxy URL.

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
