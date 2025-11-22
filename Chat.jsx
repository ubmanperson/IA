'use client'
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [csvPreview, setCsvPreview] = useState(null);

  // Check backend connection on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const res = await fetch('http://localhost:8000/health');
      if (res.ok) {
        const data = await res.json();
        setBackendStatus('connected');
        console.log('Backend connected:', data);
      } else {
        setBackendStatus('error');
      }
    } catch (error) {
      setBackendStatus('disconnected');
      console.error('Backend connection failed:', error);
    }
  };

  // Preview CSV data when file is selected
  const handleCsvFileChange = async (file) => {
    setCsvFile(file);
    if (file) {
      try {
        const text = await file.text();
        const lines = text.split('\n').filter(line => line.trim());
        const headers = lines[0].split(',');
        const previewLines = lines.slice(1, 6); // Show first 5 data rows
        
        setCsvPreview({
          headers,
          preview: previewLines,
          totalLines: lines.length - 1
        });
      } catch (error) {
        console.error('Error reading CSV:', error);
        setCsvPreview(null);
      }
    } else {
      setCsvPreview(null);
    }
  };

  // === Send Text Message ===
  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);

    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);

    const formData = new FormData();
    formData.append('prompt', input);

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      const botMessage = { sender: 'assistant', text: data.response || data.analysis };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { sender: 'system', text: '❌ Error connecting to backend. Make sure the server is running on port 8000.' }]);
    }

    setInput('');
    setLoading(false);
  };

  // === Upload CSV and Analyze ===
  const uploadCSV = async () => {
    if (!csvFile) return;
    setLoading(true);

    try {
      // Read CSV file and convert to OHLC format
      const text = await csvFile.text();
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',');
      
      // Get at least 50 lines (or all available if less than 50)
      const minLines = 50;
      const dataLines = lines.slice(1); // Skip header
      const linesToProcess = dataLines.length >= minLines ? dataLines.slice(-minLines) : dataLines;
      
      console.log(`Processing ${linesToProcess.length} lines from CSV (requested: ${minLines})`);
      
      // Convert CSV to OHLC format for the backend
      const ohlcData = linesToProcess.map(line => {
        const values = line.split(',');
        return {
          t: values[0] || new Date().toISOString(),
          open: parseFloat(values[1]) || 0,
          high: parseFloat(values[2]) || 0,
          low: parseFloat(values[3]) || 0,
          close: parseFloat(values[4]) || 0,
          volume: parseFloat(values[5]) || 0
        };
      });

      const formData = new FormData();
      formData.append('question', input || 'Analyze this CSV data');
      formData.append('ohlc_json', JSON.stringify(ohlcData));

      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      
      // Show CSV preview and analysis
      const csvPreview = `📊 CSV uploaded and analyzed\n\n📈 Data Summary:\n- Total lines processed: ${ohlcData.length}\n- Date range: ${ohlcData[0]?.t} to ${ohlcData[ohlcData.length-1]?.t}\n- Price range: $${Math.min(...ohlcData.map(d => d.low))} - $${Math.max(...ohlcData.map(d => d.high))}`;
      
      setMessages(prev => [...prev, { sender: 'system', text: csvPreview }]);
      
      if (data.analysis) {
        const botMessage = { sender: 'assistant', text: data.analysis };
        setMessages(prev => [...prev, botMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { sender: 'system', text: '❌ Failed to upload and analyze CSV' }]);
    }

    setCsvFile(null);
    setCsvPreview(null);
    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen min-w-[70rem] text-white">
      <h1 className="text-2xl font-bold mb-4">CSV Chatbot Assistant</h1>
      
      {/* Backend Status Indicator */}
      <div className="flex items-center gap-3 mb-4">
        <div className={`px-3 py-1 rounded-full text-sm ${
          backendStatus === 'connected' ? 'bg-green-600 text-white' :
          backendStatus === 'disconnected' ? 'bg-red-600 text-white' :
          backendStatus === 'error' ? 'bg-yellow-600 text-white' :
          'bg-gray-600 text-white'
        }`}>
          {backendStatus === 'connected' ? '🟢 Backend Connected' :
           backendStatus === 'disconnected' ? '🔴 Backend Disconnected' :
           backendStatus === 'error' ? '🟡 Backend Error' :
           '⚪ Checking Connection...'}
        </div>
        <button
          onClick={checkBackendHealth}
          className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Chat Container */}
      <div className="flex flex-col w-full max-w-2xl h-[70vh] bg-gray-900 rounded-2xl shadow-lg p-4">
        
        {/* File Uploads */}
        <div className="flex gap-2 mb-4">
          <div className="flex flex-col gap-2">
            <input
              type="file"
              accept=".csv"
              onChange={e => handleCsvFileChange(e.target.files[0])}
              className="text-sm text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
            />
            {csvFile && (
              <div className="text-xs text-gray-400">
                📁 {csvFile.name} ({(csvFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
            {csvPreview && (
              <div className="text-xs text-gray-300 bg-gray-800 p-2 rounded max-w-xs">
                <div className="font-semibold mb-1">📊 CSV Preview:</div>
                <div className="text-gray-400 mb-1">
                  Headers: {csvPreview.headers.join(', ')}
                </div>
                <div className="text-gray-400 mb-1">
                  Total rows: {csvPreview.totalLines}
                </div>
                <div className="text-gray-500 text-xs">
                  {csvPreview.preview.slice(0, 3).map((line, i) => (
                    <div key={i} className="truncate">{line}</div>
                  ))}
                  {csvPreview.preview.length > 3 && <div>...</div>}
                </div>
              </div>
            )}
          </div>
          <button
            onClick={uploadCSV}
            disabled={!csvFile || loading}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              csvFile && !loading ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-500 text-gray-300 cursor-not-allowed'
            }`}
          >
            Analyze CSV
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-3 mb-4 bg-gray-800 p-3 rounded">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`rounded-2xl px-4 py-2 max-w-[70%] whitespace-pre-line ${
                  msg.sender === 'user'
                    ? 'bg-blue-500 text-white'
                    : msg.sender === 'assistant'
                    ? 'bg-gray-700 text-gray-100'
                    : 'bg-gray-500 text-black'
                }`}
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            className="flex-1 border rounded px-3 py-2 bg-gray-700 text-white placeholder-gray-400 border-gray-600 focus:outline-none focus:border-blue-500"
            placeholder="Type your message..."
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className={`px-4 py-2 rounded transition-colors ${
              loading || !input.trim() 
                ? 'bg-gray-500 text-gray-300 cursor-not-allowed' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
