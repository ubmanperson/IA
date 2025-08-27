# main.py
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List
import subprocess
import json
import base64
import asyncio
import requests  # For HTTP API approach

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - choose your preferred method
OLLAMA_USE_HTTP_API = True  # Set to True to use HTTP API instead of CLI
OLLAMA_BASE_URL = "http://localhost:11434"  # Default Ollama HTTP API URL

def build_price_table(ohlc: List[dict], max_bars: int = 20) -> str:
    """Create a short, human-friendly text table from OHLC list of dicts.
    Expect each dict: {'t':'2025-08-26T12:00:00Z','open':..., 'high':..., 'low':..., 'close':..., 'volume':...}
    """
    recent = ohlc[-max_bars:]
    rows = ["time\topen\thigh\tlow\tclose\tvol"]
    for r in recent:
        rows.append(f"{r.get('t','?')}\t{r.get('open','?')}\t{r.get('high','?')}\t{r.get('low','?')}\t{r.get('close','?')}\t{r.get('volume','')}")
    return "\n".join(rows)

def make_analysis_prompt(user_question: str, ohlc: Optional[List[dict]], image_b64: Optional[str]) -> str:
    # Few-shot examples - keep these short and task-focused
    few_shot = """
Example 1:
Data: 3-bar bullish engulfing on 15m, higher lows, volume increasing.
Interpretation: Short-term bullish continuation; set stop below recent low and target initial resistance.

Example 2:
Data: Double top on 1H with bearish divergence on RSI.
Interpretation: Expect a pullback, possible trend reversal; look for confirmation candle below neckline.
"""
    prompt_parts = [
        "You are a market-structure assistant. Provide concise analysis and possible price actions with reasons. Be explicit about uncertainty and list at least 2 possible scenarios with triggers.",
        "",
        "USER QUESTION:",
        user_question,
        ""
    ]
    if ohlc:
        prompt_parts += ["RECENT PRICE DATA (most recent last):", build_price_table(ohlc), ""]
    if image_b64:
        prompt_parts += ["CHART_IMAGE: (image included)","Please analyze the visible price action on the chart. Use the numeric data if present."]

    prompt_parts += ["", "FEW-SHOT EXAMPLES:", few_shot, "", "Answer:"]
    return "\n".join(prompt_parts)

def call_ollama_http_api(prompt: str, image_b64: Optional[str] = None) -> str:
    """Call Ollama using HTTP API instead of CLI"""
    try:
        payload = {
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        if image_b64:
            payload["images"] = [image_b64]
        
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "No response from Ollama")
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP API call failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response from Ollama: {str(e)}")

def call_ollama_cli(prompt: str, image_b64: Optional[str] = None) -> str:
    """Call Ollama using CLI subprocess"""
    try:
        payload = {
            "model": "gemma3:4b",
            "prompt": prompt,
        }
        if image_b64:
            payload["images"] = [image_b64]

        # Call ollama via CLI; pass JSON on stdin and read stdout
        proc = subprocess.Popen(
            ["ollama", "run", "gemma3:4b"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(json.dumps(payload))
        
        if proc.returncode != 0:
            raise Exception(f"Ollama CLI failed: {stderr}")
        
        return stdout
    except subprocess.SubprocessError as e:
        raise Exception(f"Subprocess error: {str(e)}")

@app.post("/chat")
async def chat_endpoint(prompt: str = Form(...), image: UploadFile = File(None)):
    """Simple pass-through chat. Sends prompt and optional image to Gemma3 and returns the whole response."""
    image_b64 = None
    if image:
        content = await image.read()
        image_b64 = base64.b64encode(content).decode("utf-8")

    try:
        if OLLAMA_USE_HTTP_API:
            response = call_ollama_http_api(prompt, image_b64)
        else:
            response = call_ollama_cli(prompt, image_b64)
        
        return {"response": response}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/analyze")
async def analyze_endpoint(
    question: str = Form(...),
    ohlc_json: Optional[str] = Form(None),  # JSON string of list of OHLC dicts
    image: UploadFile = File(None),
    stream: Optional[bool] = Form(False),
):
    """Specialized price-action analysis endpoint.
       - 'ohlc_json' is optional stringified JSON of recent bars.
       - if stream=True, returns Server-Sent Events (SSE) streaming of tokens (if ollama CLI streams).
    """
    image_b64 = None
    if image:
        content = await image.read()
        image_b64 = base64.b64encode(content).decode("utf-8")

    ohlc = None
    if ohlc_json:
        try:
            ohlc = json.loads(ohlc_json)
        except Exception as e:
            return JSONResponse({"error": "Invalid ohlc_json: " + str(e)}, status_code=400)

    prompt = make_analysis_prompt(question, ohlc, image_b64)

    # Non-streaming version (simpler)
    if not stream:
        try:
            if OLLAMA_USE_HTTP_API:
                analysis = call_ollama_http_api(prompt, image_b64)
            else:
                analysis = call_ollama_cli(prompt, image_b64)
            
            return {"analysis": analysis}
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    # Streaming version using StreamingResponse
    async def event_stream():
        try:
            if OLLAMA_USE_HTTP_API:
                # HTTP API streaming implementation
                payload = {
                    "model": "gemma3:4b",
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 2048
                    }
                }
                if image_b64:
                    payload["images"] = [image_b64]
                
                # Use aiohttp for async streaming or fallback to sync requests
                try:
                    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, stream=True, timeout=120)
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk_data = json.loads(line.decode('utf-8'))
                                if 'response' in chunk_data:
                                    yield chunk_data['response']
                                if chunk_data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    # Fallback to non-streaming if streaming fails
                    response = call_ollama_http_api(prompt, image_b64)
                    yield response
            else:
                proc = await asyncio.create_subprocess_exec(
                    "ollama", "run", "gemma3:4b",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    # NOTE: if ollama has a --stream flag, add it.
                )
                # send JSON payload
                await proc.stdin.write(json.dumps({"model":"gemma3:4b","prompt":prompt}).encode())
                await proc.stdin.drain()
                await proc.stdin.close()

                while True:
                    chunk = await proc.stdout.readline()
                    if not chunk:
                        break
                    yield chunk.decode('utf-8')

                rc = await proc.wait()
                if rc != 0:
                    err = await proc.stderr.read()
                    yield f"\n[ERROR]\n{err.decode()}"
        except Exception as e:
            yield f"\n[ERROR]\n{str(e)}"
    
    return StreamingResponse(event_stream(), media_type="text/plain")

# Health check endpoint to verify Ollama connection
@app.get("/health")
async def health_check():
    """Check if Ollama is accessible"""
    try:
        if OLLAMA_USE_HTTP_API:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            models_data = response.json()
            return {
                "status": "healthy", 
                "method": "HTTP API", 
                "ollama_url": OLLAMA_BASE_URL,
                "models": [model.get("name", "") for model in models_data.get("models", [])]
            }
        else:
            # Test CLI access
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return {"status": "healthy", "method": "CLI", "models": result.stdout.strip()}
            else:
                return {"status": "unhealthy", "method": "CLI", "error": result.stderr}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# List available models
@app.get("/models")
async def list_models():
    """List all available Ollama models"""
    try:
        if OLLAMA_USE_HTTP_API:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json()
        else:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {"models": result.stdout.strip()}
            else:
                return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

# Pull a specific model
@app.post("/models/pull")
async def pull_model(model_name: str = Form(...)):
    """Pull a specific model from Ollama"""
    try:
        if OLLAMA_USE_HTTP_API:
            payload = {"name": model_name}
            response = requests.post(f"{OLLAMA_BASE_URL}/api/pull", json=payload, timeout=300)
            response.raise_for_status()
            return {"message": f"Model {model_name} pulled successfully"}
        else:
            result = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return {"message": f"Model {model_name} pulled successfully"}
            else:
                return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}