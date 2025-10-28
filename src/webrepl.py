import socket
import threading
import struct
import hashlib
import base64
import code
import sys
import io
import traceback
import webbrowser
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional, Dict, Any
import time
import random

HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Web REPL</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            height: 90vh;
            background: #1e1e1e;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            background: #2d2d30;
            padding: 15px 20px;
            border-bottom: 1px solid #3e3e42;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            color: #ffffff;
            font-size: 18px;
            font-weight: 600;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #cccccc;
            font-size: 14px;
        }

        .end-session-btn {
            background: #f48771;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }

        .end-session-btn:hover {
            background: #e67361;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(244, 135, 113, 0.3);
        }

        .end-session-btn:active {
            transform: translateY(0);
        }

        .end-session-btn:disabled {
            background: #666666;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4ec9b0;
            animation: pulse 2s infinite;
        }

        .status-indicator.disconnected {
            background: #f48771;
            animation: none;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .terminal {
            flex: 1;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            overflow-y: auto;
            font-size: 14px;
            line-height: 1.6;
            user-select: text;
        }

        .terminal::selection {
            background: #264f78;
            color: #ffffff;
        }

        .terminal::-webkit-scrollbar {
            width: 10px;
        }

        .terminal::-webkit-scrollbar-track {
            background: #1e1e1e;
        }

        .terminal::-webkit-scrollbar-thumb {
            background: #3e3e42;
            border-radius: 5px;
        }

        .terminal::-webkit-scrollbar-thumb:hover {
            background: #4e4e52;
        }

        .output-line {
            margin: 2px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            user-select: text;
            cursor: text;
        }

        .output-line::selection,
        .output-line *::selection {
            background: #264f78;
            color: #ffffff;
        }

        .banner {
            color: #4ec9b0;
            margin-bottom: 10px;
        }

        .stdout {
            color: #d4d4d4;
        }

        .stderr {
            color: #f48771;
        }

        .input-container {
            display: flex;
            align-items: flex-start;
            margin-top: 5px;
        }

        .prompt {
            color: #4ec9b0;
            margin-right: 5px;
            user-select: none;
            cursor: default;
        }

        .input-wrapper {
            flex: 1;
            position: relative;
        }

        #input {
            background: transparent;
            border: none;
            color: #d4d4d4;
            font-family: inherit;
            font-size: inherit;
            outline: none;
            width: 100%;
            caret-color: #d4d4d4;
            position: relative;
            z-index: 2;
            resize: none;
            min-height: 20px;
            max-height: 300px;
            overflow-y: auto;
            line-height: 1.6;
        }

        #input-highlight {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            pointer-events: none;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow: hidden;
            z-index: 1;
            line-height: 1.6;
        }

        #input.has-highlight {
            color: transparent;
            caret-color: #d4d4d4;
        }

        #input::-webkit-scrollbar {
            width: 6px;
        }

        #input::-webkit-scrollbar-track {
            background: transparent;
        }

        #input::-webkit-scrollbar-thumb {
            background: #3e3e42;
            border-radius: 3px;
        }

        .cursor {
            display: inline-block;
            width: 8px;
            height: 18px;
            background: #d4d4d4;
            animation: blink 1s step-end infinite;
            vertical-align: text-bottom;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        .footer {
            background: #2d2d30;
            padding: 10px 20px;
            border-top: 1px solid #3e3e42;
            color: #858585;
            font-size: 12px;
            text-align: center;
        }

        .connection-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(30, 30, 30, 0.95);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .connection-message {
            text-align: center;
            color: #d4d4d4;
        }

        .connection-message h2 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #4ec9b0;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #3e3e42;
            border-top: 4px solid #4ec9b0;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hidden {
            display: none;
        }

        .confirm-dialog {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            animation: fadeIn 0.2s;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .confirm-content {
            background: #2d2d30;
            border-radius: 12px;
            padding: 30px;
            max-width: 400px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: slideIn 0.3s;
        }

        @keyframes slideIn {
            from { transform: translateY(-20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .confirm-content h3 {
            color: #ffffff;
            font-size: 20px;
            margin-bottom: 15px;
        }

        .confirm-content p {
            color: #cccccc;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 25px;
        }

        .confirm-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .confirm-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }

        .confirm-btn-cancel {
            background: #3e3e42;
            color: #ffffff;
        }

        .confirm-btn-cancel:hover {
            background: #4e4e52;
        }

        .confirm-btn-confirm {
            background: #f48771;
            color: #ffffff;
        }

        .confirm-btn-confirm:hover {
            background: #e67361;
        }

        .code-highlight {
            display: inline;
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            font-family: inherit;
            font-size: inherit;
            line-height: inherit;
        }

        .code-highlight code {
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            font-family: inherit;
            font-size: inherit;
            color: inherit;
        }

        .token.keyword {
            color: #c586c0 !important;
        }

        .token.string {
            color: #ce9178 !important;
        }

        .token.number {
            color: #b5cea8 !important;
        }

        .token.function {
            color: #dcdcaa !important;
        }

        .token.class-name {
            color: #4ec9b0 !important;
        }

        .token.comment {
            color: #6a9955 !important;
            font-style: italic;
        }

        .token.operator {
            color: #d4d4d4 !important;
        }

        .token.punctuation {
            color: #d4d4d4 !important;
        }

        .token.builtin {
            color: #4ec9b0 !important;
        }

        .token.boolean {
            color: #569cd6 !important;
        }

        .input-line-code {
            display: inline;
            user-select: text;
        }

        ::selection {
            background: #264f78;
            color: #ffffff;
        }

        ::-moz-selection {
            background: #264f78;
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐍 Python Web REPL</h1>
            <div class="header-right">
                <div class="status">
                    <div class="status-indicator" id="statusIndicator"></div>
                    <span id="statusText">Connected</span>
                </div>
                <button class="end-session-btn" id="endSessionBtn">End Session</button>
            </div>
        </div>

        <div class="terminal" id="terminal">
        </div>

        <div class="footer">
            Press Enter to execute code | Shift+Enter for new line | ↑/↓ to browse history | Click "End Session" button or Ctrl+C in terminal to end REPL
        </div>

        <div class="connection-overlay" id="connectionOverlay">
            <div class="connection-message">
                <h2>Connecting to Python...</h2>
                <div class="spinner"></div>
                <p>Please ensure Python Web REPL server is running</p>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>

    <script>
        class WebREPL {
            constructor() {
                this.ws = null;
                this.terminal = document.getElementById('terminal');
                this.statusIndicator = document.getElementById('statusIndicator');
                this.statusText = document.getElementById('statusText');
                this.connectionOverlay = document.getElementById('connectionOverlay');
                this.endSessionBtn = document.getElementById('endSessionBtn');
                this.currentPrompt = '>>> ';
                this.history = [];
                this.historyIndex = -1;
                this.currentInput = '';
                this.sessionEnded = false;
                
                this.connect();
                this.setupEndSessionButton();
                this.setupBeforeUnload();
            }

            connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}`;
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    this.updateStatus(true);
                    this.connectionOverlay.classList.add('hidden');
                    this.createInputLine();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };

                this.ws.onclose = () => {
                    this.updateStatus(false);
                    this.removeInputLine();
                    this.appendOutput('\n\n[Connection closed]\n', 'stderr');
                };
            }

            updateStatus(connected) {
                if (connected) {
                    this.statusIndicator.classList.remove('disconnected');
                    this.statusText.textContent = 'Connected';
                    this.endSessionBtn.disabled = false;
                } else {
                    this.statusIndicator.classList.add('disconnected');
                    this.statusText.textContent = 'Disconnected';
                    this.endSessionBtn.disabled = true;
                }
            }

            setupEndSessionButton() {
                this.endSessionBtn.addEventListener('click', () => {
                    if (this.sessionEnded) return;
                    this.showConfirmDialog();
                });
            }

            showConfirmDialog() {
                const dialog = document.createElement('div');
                dialog.className = 'confirm-dialog';
                dialog.innerHTML = `
                    <div class="confirm-content">
                        <h3>🛑 End REPL Session</h3>
                        <p>Are you sure you want to end the current REPL session?</p>
                        <p style="font-size: 13px; color: #999;">After ending, the Python program will continue executing subsequent code.</p>
                        <div class="confirm-buttons">
                            <button class="confirm-btn confirm-btn-cancel" id="cancelBtn">Cancel</button>
                            <button class="confirm-btn confirm-btn-confirm" id="confirmBtn">Confirm</button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(dialog);
                
                document.getElementById('cancelBtn').addEventListener('click', () => {
                    dialog.remove();
                });
                
                document.getElementById('confirmBtn').addEventListener('click', () => {
                    dialog.remove();
                    this.endSession();
                });
                
                dialog.addEventListener('click', (e) => {
                    if (e.target === dialog) {
                        dialog.remove();
                    }
                });
                
                const escHandler = (e) => {
                    if (e.key === 'Escape') {
                        dialog.remove();
                        document.removeEventListener('keydown', escHandler);
                    }
                };
                document.addEventListener('keydown', escHandler);
            }

            endSession() {
                this.sessionEnded = true;
                this.removeInputLine();
                this.appendOutput('\n[User ended session]\n', 'banner');
                
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send('__CLOSE__');
                    this.ws.close();
                }
                
                this.endSessionBtn.textContent = 'Session Ended';
                this.endSessionBtn.disabled = true;
            }

            handleMessage(message) {
                const colonIndex = message.indexOf(':');
                if (colonIndex === -1) return;

                const type = message.substring(0, colonIndex);
                const content = message.substring(colonIndex + 1);

                if (type === 'prompt') {
                    this.currentPrompt = content;
                    this.createInputLine();
                } else {
                    this.appendOutput(content, type);
                }
            }

            appendOutput(text, className) {
                const line = document.createElement('div');
                line.className = `output-line ${className}`;
                line.textContent = text;
                
                const inputContainer = document.querySelector('.input-container');
                if (inputContainer) {
                    inputContainer.remove();
                }
                
                this.terminal.appendChild(line);
                this.scrollToBottom();
            }

            createInputLine() {
                this.removeInputLine();

                const container = document.createElement('div');
                container.className = 'input-container';

                const prompt = document.createElement('span');
                prompt.className = 'prompt';
                prompt.textContent = this.currentPrompt;

                const wrapper = document.createElement('div');
                wrapper.className = 'input-wrapper';

                const highlight = document.createElement('div');
                highlight.id = 'input-highlight';

                const input = document.createElement('textarea');
                input.id = 'input';
                input.autocomplete = 'off';
                input.spellcheck = false;
                input.rows = 1;

                wrapper.appendChild(highlight);
                wrapper.appendChild(input);
                container.appendChild(prompt);
                container.appendChild(wrapper);
                this.terminal.appendChild(container);

                input.focus();
                this.setupInputHandlers(input);
                this.setupLiveHighlight(input, highlight);
                this.scrollToBottom();
            }

            setupLiveHighlight(input, highlight) {
                const updateHighlight = () => {
                    const code = input.value;
                    if (code.trim()) {
                        highlight.innerHTML = this.highlightPython(code);
                        input.classList.add('has-highlight');
                    } else {
                        highlight.innerHTML = '';
                        input.classList.remove('has-highlight');
                    }
                    
                    this.autoResizeTextarea(input);
                };

                input.addEventListener('input', updateHighlight);
                input.addEventListener('keyup', updateHighlight);
            }

            autoResizeTextarea(textarea) {
                textarea.style.height = 'auto';
                const newHeight = Math.min(textarea.scrollHeight, 300);
                textarea.style.height = newHeight + 'px';
            }

            removeInputLine() {
                const inputContainer = document.querySelector('.input-container');
                if (inputContainer) {
                    inputContainer.remove();
                }
            }

            setupInputHandlers(input) {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        if (e.shiftKey) {
                        } else {
                            e.preventDefault();
                            this.sendCommand(input.value);
                            input.value = '';
                            this.historyIndex = -1;
                            
                            input.style.height = 'auto';
                            const highlight = document.getElementById('input-highlight');
                            if (highlight) {
                                highlight.innerHTML = '';
                            }
                            input.classList.remove('has-highlight');
                        }
                    } else if (e.key === 'ArrowUp') {
                        const cursorPosition = input.selectionStart;
                        const textBeforeCursor = input.value.substring(0, cursorPosition);
                        const isFirstLine = !textBeforeCursor.includes('\n');
                        
                        if (isFirstLine && this.historyIndex < this.history.length - 1) {
                            e.preventDefault();
                            if (this.historyIndex === -1) {
                                this.currentInput = input.value;
                            }
                            this.historyIndex++;
                            input.value = this.history[this.history.length - 1 - this.historyIndex];
                            
                            this.autoResizeTextarea(input);
                            const highlight = document.getElementById('input-highlight');
                            if (highlight && input.value.trim()) {
                                highlight.innerHTML = this.highlightPython(input.value);
                                input.classList.add('has-highlight');
                            }
                        }
                    } else if (e.key === 'ArrowDown') {
                        const cursorPosition = input.selectionStart;
                        const textAfterCursor = input.value.substring(cursorPosition);
                        const isLastLine = !textAfterCursor.includes('\n');
                        
                        if (isLastLine && this.historyIndex >= 0) {
                            e.preventDefault();
                            if (this.historyIndex > 0) {
                                this.historyIndex--;
                                input.value = this.history[this.history.length - 1 - this.historyIndex];
                            } else if (this.historyIndex === 0) {
                                this.historyIndex = -1;
                                input.value = this.currentInput;
                            }
                            
                            this.autoResizeTextarea(input);
                            const highlight = document.getElementById('input-highlight');
                            if (highlight && input.value.trim()) {
                                highlight.innerHTML = this.highlightPython(input.value);
                                input.classList.add('has-highlight');
                            } else if (highlight) {
                                highlight.innerHTML = '';
                                input.classList.remove('has-highlight');
                            }
                        }
                    }
                });

                this.terminal.addEventListener('click', (e) => {
                    const currentInput = document.getElementById('input');
                    if (!currentInput) return;
                    
                    const selection = window.getSelection();
                    if (selection && selection.toString().length > 0) {
                        return;
                    }
                    
                    const target = e.target;
                    if (target.tagName === 'BUTTON' || 
                        target.tagName === 'INPUT' || 
                        target.tagName === 'TEXTAREA' ||
                        target.closest('button')) {
                        return;
                    }
                    
                    currentInput.focus();
                });
            }

            sendCommand(command) {
                const line = document.createElement('div');
                line.className = 'output-line';
                
                const promptSpan = document.createElement('span');
                promptSpan.className = 'prompt';
                promptSpan.textContent = this.currentPrompt;
                
                const codeSpan = document.createElement('span');
                codeSpan.className = 'input-line-code';
                codeSpan.innerHTML = this.highlightPython(command);
                
                line.appendChild(promptSpan);
                line.appendChild(codeSpan);
                
                this.removeInputLine();
                this.terminal.appendChild(line);
                
                if (command.trim()) {
                    this.history.push(command);
                }

                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(command);
                }

                this.scrollToBottom();
            }

            highlightPython(code) {
                try {
                    const highlighted = Prism.highlight(code, Prism.languages.python, 'python');
                    return highlighted;
                } catch (e) {
                    return this.escapeHtml(code);
                }
            }

            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            scrollToBottom() {
                this.terminal.scrollTop = this.terminal.scrollHeight;
            }

            setupBeforeUnload() {
                window.addEventListener('beforeunload', (e) => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN && !this.sessionEnded) {
                        e.preventDefault();
                        e.returnValue = '';
                        return '';
                    }
                });

                window.addEventListener('unload', () => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send('__CLOSE__');
                        this.ws.close();
                    }
                });
            }
        }

        const repl = new WebREPL();
    </script>
</body>
</html>
"""

class UnifiedServer:
    """Unified HTTP/WebSocket server"""
    
    def __init__(self, host: str, port: int, repl_handler):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.repl_handler = repl_handler
        
    def start(self):
        """Start the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"Server running at http://{self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    thread = threading.Thread(
                        target=self.handle_connection, 
                        args=(client_socket, address),
                        daemon=True
                    )
                    thread.start()
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}", file=sys.stderr)
                    
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
    
    def handle_connection(self, client_socket: socket.socket, address):
        """Handle client connection, determine if HTTP or WebSocket"""
        try:
            request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
            
            if not request_data:
                return
            
            lines = request_data.split('\r\n')
            if not lines:
                return
            
            headers = {}
            request_line = lines[0]
            
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            is_websocket = (
                headers.get('upgrade', '').lower() == 'websocket' and
                headers.get('connection', '').lower().find('upgrade') != -1
            )
            
            if is_websocket:
                self.handle_websocket(client_socket, address, request_data)
            else:
                self.handle_http(client_socket, request_line)
                
        except Exception as e:
            print(f"Error handling connection: {e}", file=sys.stderr)
            try:
                client_socket.close()
            except:
                pass
    
    def handle_http(self, client_socket: socket.socket, request_line: str):
        try:
            parts = request_line.split()
            
            if len(parts) < 2:
                self.send_http_response(client_socket, 400, 'Bad Request',
                                       'text/plain', b'400 Bad Request')
                return
            
            method = parts[0]
            path = parts[1]
            
            if method != 'GET':
                self.send_http_response(client_socket, 405, 'Method Not Allowed', 
                                       'text/plain', b'405 Method Not Allowed')
                return
            
            if path == '/' or path == '/index.html':
                html_bytes = HTML_CONTENT.encode('utf-8')
                self.send_http_response(client_socket, 200, 'OK', 
                                       'text/html; charset=utf-8', html_bytes)
            else:
                self.send_http_response(client_socket, 404, 'Not Found', 
                                       'text/plain', b'404 Not Found')
                
        except Exception as e:
            try:
                self.send_http_response(client_socket, 500, 'Internal Server Error',
                                       'text/plain', b'500 Internal Server Error')
            except:
                pass
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def handle_websocket(self, client_socket: socket.socket, address, request_data: str):
        try:
            ws = WebSocketConnection(client_socket, address)
            
            if ws.do_handshake_with_data(request_data):
                print(f"WebSocket client connected: {address}")
                if self.repl_handler:
                    self.repl_handler.handle_websocket_client(ws)
            else:
                print(f"WebSocket handshake failed: {address}")
                ws.close()
        except Exception as e:
            print(f"WebSocket handling error: {e}", file=sys.stderr)
    
    def send_http_response(self, client_socket: socket.socket, status_code: int, 
                          status_text: str, content_type: str, body: bytes):
        try:
            response = f'HTTP/1.1 {status_code} {status_text}\r\n'
            response += f'Content-Type: {content_type}\r\n'
            response += f'Content-Length: {len(body)}\r\n'
            response += 'Connection: close\r\n'
            response += '\r\n'
            
            client_socket.sendall(response.encode('utf-8') + body)
        except Exception as e:
            pass
    
    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class WebSocketConnection:
    
    def __init__(self, client_socket, address):
        self.socket = client_socket
        self.address = address
        self.handshake_done = False
        
    def do_handshake(self):
        try:
            request = self.socket.recv(4096).decode('utf-8')
            return self.do_handshake_with_data(request)
        except Exception as e:
            print(f"Handshake failed: {e}", file=sys.stderr)
            return False
    
    def do_handshake_with_data(self, request: str):
        try:
            headers = {}
            lines = request.split('\r\n')
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            websocket_key = headers.get('Sec-WebSocket-Key')
            if not websocket_key:
                return False
            
            magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + magic_string).encode()).digest()
            ).decode()
            
            response = (
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {accept_key}\r\n'
                '\r\n'
            )
            self.socket.sendall(response.encode())
            self.handshake_done = True
            return True
            
        except Exception as e:
            print(f"Handshake failed: {e}", file=sys.stderr)
            return False
    
    def recv_frame(self):
        """Receive WebSocket frame"""
        try:
            header = self.socket.recv(2)
            if len(header) < 2:
                return None
            
            byte1, byte2 = struct.unpack('BB', header)
            
            fin = (byte1 & 0x80) != 0
            opcode = byte1 & 0x0F
            masked = (byte2 & 0x80) != 0
            payload_length = byte2 & 0x7F
            
            if opcode == 0x8:
                return None
            
            if opcode == 0x9:
                self.send_pong()
                return self.recv_frame()
            
            if opcode not in (0x1, 0x0):
                return self.recv_frame()
            
            if payload_length == 126:
                extended = self.socket.recv(2)
                payload_length = struct.unpack('>H', extended)[0]
            elif payload_length == 127:
                extended = self.socket.recv(8)
                payload_length = struct.unpack('>Q', extended)[0]
            
            if masked:
                masking_key = self.socket.recv(4)
            
            payload = bytearray()
            remaining = payload_length
            while remaining > 0:
                chunk = self.socket.recv(min(remaining, 4096))
                if not chunk:
                    return None
                payload.extend(chunk)
                remaining -= len(chunk)
            
            if masked:
                for i in range(len(payload)):
                    payload[i] ^= masking_key[i % 4]
            
            return payload.decode('utf-8')
            
        except Exception as e:
            return None
    
    def send_frame(self, message):
        try:
            message_bytes = message.encode('utf-8')
            length = len(message_bytes)
            
            frame = bytearray()
            frame.append(0x81)
            
            if length <= 125:
                frame.append(length)
            elif length <= 65535:
                frame.append(126)
                frame.extend(struct.pack('>H', length))
            else:
                frame.append(127)
                frame.extend(struct.pack('>Q', length))
            
            frame.extend(message_bytes)
            
            self.socket.sendall(frame)
            return True
            
        except Exception as e:
            return False
    
    def send_pong(self):
        try:
            frame = bytearray([0x8A, 0x00])
            self.socket.sendall(frame)
        except:
            pass
    
    def close(self):
        try:
            frame = bytearray([0x88, 0x00])
            self.socket.sendall(frame)
        except:
            pass
        finally:
            try:
                self.socket.close()
            except:
                pass


def find_free_port(host: str, preferred_port: Optional[int] = None, 
                   min_port: int = 8000, max_port: int = 9000) -> int:
    if preferred_port is not None:
        if is_port_available(host, preferred_port):
            return preferred_port
    
    tried_ports = set()
    max_attempts = 100
    
    for _ in range(max_attempts):
        port = random.randint(min_port, max_port)
        if port in tried_ports:
            continue
        tried_ports.add(port)
        
        if is_port_available(host, port):
            return port
    
    for port in range(min_port, max_port + 1):
        if port not in tried_ports and is_port_available(host, port):
            return port
    
    raise RuntimeError(f"Unable to find available port in range {min_port}-{max_port}")


def is_port_available(host: str, port: int) -> bool:
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((host, port))
        test_socket.close()
        return True
    except OSError:
        return False


class WebREPL:
    def __init__(self, local: Optional[Dict[str, Any]] = None, 
                 banner: Optional[str] = None,
                 host: str = "localhost",
                 port: Optional[int] = None,
                 echo_terminal: bool = False):
        self.host = host
        self.port_preference = port
        self.port = None
        self.auto_port = (port is None)
        self.echo_terminal = echo_terminal
        
        self.local = local if local is not None else {}
        self.banner = banner if banner is not None else (
            f"Python {sys.version} on {sys.platform}\n"
            f"Web REPL - Run Python code in your browser\n"
            f'Type "help", "copyright", "credits" or "license" for more information.'
        )
        self.server = None
        self.running = False
        self.client_connected = threading.Event()
        self.client_closed = threading.Event()
        
    def send_output(self, ws: WebSocketConnection, text: str, output_type: str = "stdout"):
        try:
            ws.send_frame(f"{output_type}:{text}")
        except Exception as e:
            print(f"Error sending output: {e}", file=sys.__stderr__)
    
    def handle_websocket_client(self, ws: WebSocketConnection):
        self.client_connected.set()
        self.handle_client(ws)
    
    def handle_client(self, ws: WebSocketConnection):
        try:
            self.send_output(ws, self.banner + "\n", "banner")
            self.send_output(ws, ">>> ", "prompt")
            
            if self.echo_terminal:
                print(self.banner, file=sys.__stdout__)
                print(">>> ", end="", flush=True, file=sys.__stdout__)
            
            console = code.InteractiveConsole(locals=self.local)
            buffer = []
            
            while self.running:
                message = ws.recv_frame()
                if message is None:
                    break
                
                if message == "__CLOSE__":
                    break
                
                if self.echo_terminal:
                    if buffer:
                        print(message, file=sys.__stdout__)
                        print("... ", end="", flush=True, file=sys.__stdout__)
                    else:
                        print(message, file=sys.__stdout__)
                
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()
                
                try:
                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        buffer.append(message)
                        source = "\n".join(buffer)
                        
                        try:
                            compiled = code.compile_command(source)
                        except (OverflowError, SyntaxError, ValueError):
                            buffer = []
                            traceback.print_exc(file=sys.stdout)
                            compiled = False
                        
                        if compiled is None:
                            self.send_output(ws, "... ", "prompt")
                            continue
                        else:
                            buffer = []
                            if compiled:
                                try:
                                    exec(compiled, self.local)
                                except SystemExit:
                                    raise
                                except:
                                    traceback.print_exc(file=sys.stdout)
                    
                    stdout_text = stdout_capture.getvalue()
                    stderr_text = stderr_capture.getvalue()
                    
                    if stdout_text:
                        self.send_output(ws, stdout_text, "stdout")
                        if self.echo_terminal:
                            print(stdout_text, end="", file=sys.__stdout__)
                    if stderr_text:
                        self.send_output(ws, stderr_text, "stderr")
                        if self.echo_terminal:
                            print(stderr_text, end="", file=sys.__stderr__)
                    
                    self.send_output(ws, ">>> ", "prompt")
                    
                    if self.echo_terminal:
                        print(">>> ", end="", flush=True, file=sys.__stdout__)
                    
                except Exception as e:
                    self.send_output(ws, f"Internal error: {e}\n", "stderr")
                    self.send_output(ws, ">>> ", "prompt")
                    if self.echo_terminal:
                        print(f"Internal error: {e}", file=sys.__stderr__)
                        print(">>> ", end="", flush=True, file=sys.__stdout__)
        
        except Exception as e:
            print(f"Client handling error: {e}", file=sys.stderr)
        finally:
            ws.close()
            self.client_closed.set()
    
    def start_server(self):
        try:
            if self.port is None:
                self.port = find_free_port(self.host, self.port_preference)
                if self.port_preference is not None and self.port != self.port_preference:
                    print(f"Port {self.port_preference} is in use, using port {self.port}")
            
            self.server = UnifiedServer(self.host, self.port, self)
            self.running = True
            
            server_thread = threading.Thread(target=self.server.start, daemon=True)
            server_thread.start()
            
            time.sleep(0.5)
            
            print(f"Opening browser...")
            webbrowser.open(f"http://{self.host}:{self.port}")
            
            print("Waiting for client connection...")
            self.client_connected.wait()
            print("Client connected")
            
            self.client_closed.wait()
            print("Client disconnected, Web REPL ended")
            
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
            traceback.print_exc()
        finally:
            self.running = False
    
    def interact(self):
        try:
            self.start_server()
        except KeyboardInterrupt:
            print("\n\nWeb REPL interrupted")
            self.running = False
        finally:
            if self.server:
                try:
                    self.server.stop()
                except:
                    pass


def interact(banner: Optional[str] = None, 
             readfunc: Optional[Any] = None,
             local: Optional[Dict[str, Any]] = None,
             exitmsg: Optional[str] = None,
             host: str = "localhost",
             port: Optional[int] = None,
             echo_terminal: bool = False):
    """
    Start Web REPL interactive session
    
    This function mimics the code.interact() interface but uses a Web UI
    
    Args:
        banner: Welcome banner (optional)
        readfunc: Compatibility parameter, not used
        local: Local namespace dictionary
        exitmsg: Exit message (optional)
        host: Server host
        port: Server port (None means auto-select a random free port)
              HTTP and WebSocket share the same port
        echo_terminal: Whether to echo browser input/output to terminal (default: False)
    """
    if local is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            local = frame.f_back.f_locals
        else:
            local = {}
    
    repl = WebREPL(local=local, banner=banner, host=host, port=port, echo_terminal=echo_terminal)
    repl.interact()
    
    if exitmsg:
        print(exitmsg)
