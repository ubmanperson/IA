# Project Requirements and Dependencies

## Overview
This is a full-stack web application with a Next.js frontend and FastAPI backend that uses Ollama (Gemma3:4b model) for AI-powered CSV and chat analysis.

---

## Backend Requirements (Python)

### System Requirements
- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux

### Python Dependencies
Located in `requirements.txt`:

```
fastapi==0.115.0          # Web framework for building APIs
uvicorn[standard]==0.30.6  # ASGI server for running FastAPI
python-multipart==0.0.9    # Form data handling
pydantic==2.9.2            # Data validation
requests==2.32.3           # HTTP library for Ollama API
```

### Installation
```bash
pip install -r requirements.txt
```

### External Services Required
- **Ollama**: Must be installed and running
  - Download from: https://ollama.ai
  - Model required: `gemma3:4b`
  - Installation: `ollama pull gemma3:4b`
  - Service must run on: http://localhost:11434

### Backend API Endpoints

1. **POST `/chat`**
   - Accepts: `prompt` (form data), optional `image` (file)
   - Returns: `{ "response": "..." }`
   - Purpose: Simple text chat with optional image support

2. **POST `/analyze`**
   - Accepts: `question` (form data), `ohlc_json` (optional), `image` (optional), `stream` (optional boolean)
   - Returns: `{ "analysis": "..." }` or streaming response
   - Purpose: Specialized CSV price action analysis

3. **GET `/health`**
   - Returns: Status of Ollama connection
   - Purpose: Health check endpoint

4. **GET `/models`**
   - Returns: List of available Ollama models
   - Purpose: Model management

5. **POST `/models/pull`**
   - Accepts: `model_name` (form data)
   - Returns: Pull status
   - Purpose: Download new models

---

## Frontend Requirements (Next.js/React)

### System Requirements
- **Node.js**: 16.8 or higher (recommended: 18.x or later)
- **npm**: 7.0 or higher

### Production Dependencies
Located in `package.json`:

```json
{
  "next": "15.5.0",
  "react": "19.1.0",
  "react-dom": "19.1.0",
  "react-markdown": "^10.1.0",
  "remark-gfm": "^4.0.1",
  "postcss": "^8.5.6"
}
```

### Development Dependencies
```json
{
  "@eslint/eslintrc": "^3",
  "@tailwindcss/postcss": "^4.1.12",
  "eslint": "^9",
  "eslint-config-next": "15.5.0",
  "tailwindcss": "^4.1.12"
}
```

### Installation
```bash
npm install
```

### Features Implemented
- CSV file upload and preview
- Real-time chat interface
- Markdown rendering in chat messages
- Backend connection status indicator
- Tailwind CSS styling
- Responsive design

---

## Project Structure

```
ia/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Main API application
├── components/          # React components
│   └── Chat.jsx         # Main chat interface
├── src/app/            # Next.js pages
│   ├── page.jsx         # Home page
│   ├── layout.jsx       # App layout
│   └── globals.css      # Global styles
├── requirements.txt     # Python dependencies
├── package.json         # Node.js dependencies
├── tailwind.config.js   # Tailwind configuration
├── next.config.mjs      # Next.js configuration
└── postcss.config.mjs   # PostCSS configuration```

---

## Runtime Requirements

### Required Ports
- **Backend**: 8000 (FastAPI/Uvicorn)
- **Frontend**: 3000 (Next.js dev server)
- **Ollama**: 11434 (Ollama HTTP API)

### Environment Variables
None required - all configurations are hardcoded in the application.

### Configuration Files
- `tailwind.config.js` - Tailwind CSS paths
- `next.config.mjs` - Next.js configuration
- `postcss.config.mjs` - PostCSS configuration
- `eslint.config.mjs` - ESLint configuration
- `jsconfig.json` - JavaScript/JSX configuration

---

## Installation Steps

### 1. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies
```bash
npm install
```

### 3. Install and Setup Ollama
```bash
# Download from https://ollama.ai
# Or using winget on Windows:
winget install Ollama.Ollama

# Pull the required model
ollama pull gemma3:4b

# Start Ollama service
ollama serve
```

### 4. Start Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Or double-click `start_backend.bat` on Windows.

### 5. Start Frontend
```bash
npm run dev
```

---

## CSV Format Requirements

For CSV analysis to work, files should have the following format:

```csv
timestamp,open,high,low,close,volume
2025-01-01T00:00:00Z,100.5,101.2,99.8,100.9,1000000
2025-01-01T01:00:00Z,100.9,102.1,100.5,101.8,1200000
...
```

Expected columns (in order):
1. **timestamp** - ISO 8601 format
2. **open** - Opening price (float)
3. **high** - Highest price (float)
4. **low** - Lowest price (float)
5. **close** - Closing price (float)
6. **volume** - Trading volume (float)

The application processes the last 50 rows by default.

---

## Browser Compatibility

- Modern browsers with ES6+ support
- Chrome, Firefox, Edge, Safari (latest versions)
- Mobile responsive design included

---

## Development Scripts

### Frontend
```bash
npm run dev        # Start development server
npm run build      # Build for production
npm start          # Start production server
npm run lint       # Run ESLint
```

### Backend
```bash
cd backend
python -m uvicorn main:app --reload
```

---

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is available

### Frontend won't start
- Ensure Node.js 16.8+ is installed
- Install dependencies: `npm install`
- Check if port 3000 is available

### Ollama connection issues
- Verify Ollama is running: `ollama serve`
- Check if model is installed: `ollama list`
- Test API: `curl http://localhost:11434/api/tags`

### CSV upload issues
- Verify CSV format matches expected structure
- Check browser console for errors
- Ensure backend is running on port 8000

---

## Additional Notes

- The backend uses CORS middleware to allow requests from `http://localhost:3000`
- All AI processing is done via Ollama HTTP API
- The application supports streaming responses (configured but not actively used in frontend)
- Database support is included but not actively used in the current implementation


