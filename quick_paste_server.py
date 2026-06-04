#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from datetime import datetime

class TransferHandler(BaseHTTPRequestHandler):
    clipboard = ""  # Shared clipboard between all connections
    
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f'''
            <html>
            <head>
                <title>Quick Paste</title>
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                        margin: 40px;
                        background: #f5f5f5;
                        color: #333;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    textarea {{ 
                        width: 100%; 
                        height: 200px; 
                        margin: 10px 0; 
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        font-family: inherit;
                    }}
                    .buttons {{ 
                        margin: 10px 0; 
                    }}
                    button {{ 
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                        margin-right: 10px;
                    }}
                    button:hover {{
                        background: #0056b3;
                    }}
                    #status {{
                        margin-top: 10px;
                        color: #28a745;
                    }}
                    .help {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        color: #666;
                    }}
                    pre {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 4px;
                        overflow-x: auto;
                    }}
                </style>
                <script>
                    function sendText() {{
                        const text = document.getElementById('pasteArea').value;
                        fetch('/paste', {{
                            method: 'POST',
                            body: text
                        }}).then(() => {{
                            document.getElementById('status').textContent = 'Sent!';
                            setTimeout(() => {{
                                document.getElementById('status').textContent = '';
                            }}, 2000);
                        }});
                    }}
                    
                    function getText() {{
                        fetch('/paste')
                            .then(response => response.text())
                            .then(text => {{
                                document.getElementById('pasteArea').value = text;
                                document.getElementById('status').textContent = 'Retrieved!';
                                setTimeout(() => {{
                                    document.getElementById('status').textContent = '';
                                }}, 2000);
                            }});
                    }}

                    // Auto-refresh the text area every 5 seconds
                    setInterval(getText, 5000);
                </script>
            </head>
            <body>
                <div class="container">
                    <h2>Quick Paste Transfer</h2>
                    <textarea id="pasteArea" placeholder="Paste text here..."></textarea>
                    <div class="buttons">
                        <button onclick="sendText()">Send Text</button>
                        <button onclick="getText()">Get Latest Text</button>
                    </div>
                    <div id="status"></div>
                    
                    <div class="help">
                        <h3>Command Line Usage:</h3>
                        <pre>
# To send text from clipboard (MacOS):
pbpaste | curl -X POST --data-binary @- http://localhost:8000/paste

# To get text:
curl http://localhost:8000/paste
                        </pre>
                    </div>
                </div>
            </body>
            </html>
            '''
            self.wfile.write(html.encode())
            
        elif self.path == "/paste":
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(self.__class__.clipboard.encode())

    def do_POST(self):
        if self.path == "/paste":
            content_length = int(self.headers['Content-Length'])
            self.__class__.clipboard = self.rfile.read(content_length).decode('utf-8')
            self.send_response(200)
            self.end_headers()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TransferHandler)
    local_ip = get_local_ip()

    print(f"\nQuick Paste Server Running")
    print(f"==============================")
    print(f"Local Access: http://{local_ip}:{port}")
    print("\nCommand line usage:")
    print(f"Send:   pbpaste | curl -X POST --data-binary @- http://{local_ip}:{port}/paste")
    print(f"Get:    curl http://{local_ip}:{port}/paste")
    print(f"\nPress Ctrl+C to stop the server\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()