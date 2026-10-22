# ♻️ EcoScan AI

AI Waste Sorting Assistant for university campus waste management.

## Project Flow

Upload Image
↓
Gemini Vision
↓
Structured JSON
↓
RAG Retrieval
↓
Knowledge Base
↓
Disposal Recommendation

## Features

- Waste image classification
- Gemini multimodal vision
- Confidence score
- Contamination detection
- RAG-based knowledge retrieval
- Disposal recommendation
- Streamlit web interface

## Project Structure

EcoScan-AI/
├── app.py
├── knowledge_base.py
├── requirements.txt
├── README.md
└── .gitignore

## Installation

pip install -r requirements.txt

## API Key

Create the following file:

.streamlit/secrets.toml

Add:

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

Do NOT upload your API key to GitHub.

## Run

streamlit run app.py

## AI Architecture

Gemini multimodal vision analyzes the uploaded waste image.

The vision model returns:
- Item name
- Waste category
- Contamination level
- Confidence score

The category is then used to retrieve the relevant disposal rule from the Knowledge Base.

The final recommendation is generated using the retrieved information.

## Current Prototype

Waste categories:
- Recyclable
- General
- Organic
- Hazardous

The Knowledge Base currently contains prototype disposal rules and can later be expanded with real university campus disposal rules.
