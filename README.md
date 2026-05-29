# DISC Personality Assessment App 👤

**A modern DISC personality assessment app built with Streamlit and Python for generating personalized DISC profiles.**

## Features

- **Personalized DISC profiles**: Discover your unique personality style based on the DISC framework.
- **Interactive UI**: Powered by Streamlit for easy navigation and a user-friendly experience.
- **Style descriptions**: Provides detailed descriptions of single and combination styles.
- **Secure result links**: Admin can open completed evaluations with a signed URL token.
- **Direct PDF download in shared view**: Shared result view exposes PDF download (JSON hidden).
- **PDF and JSON Export (admin dashboard)**: Internal admin views keep full export options where applicable.

## Getting Started

### Prerequisites

- **Python 3.10+**
- **pip** for installing Python packages

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/dzyla/disc-personality-assessment.git
   ```
2. Navigate into the project directory:
   ```bash
   cd disc-personality-assessment
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

To run the app locally, use Streamlit:

```bash
streamlit run app.py
```

This will start the application and open it in your browser. Follow the prompts to complete the DISC assessment.

## Usage

The app will guide users through a series of questions, after which it calculates the DISC profile based on their answers. Users can:

- View their DISC style profile in a visual format.
- Read detailed descriptions of their primary and secondary styles.
- Download their results as a PDF or JSON file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
