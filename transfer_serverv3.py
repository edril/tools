#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import socket
import argparse
from datetime import datetime
import email
from email.parser import BytesParser
import tempfile

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

class TransferHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Get files with their details
            files = []
            for f in os.listdir('.'):
                if os.path.isfile(f):
                    stats = os.stat(f)
                    # Store raw values for proper sorting
                    files.append({
                        'name': f,
                        'raw_size': stats.st_size,  # Raw size for sorting
                        'size': format_size(stats.st_size),  # Formatted size for display
                        'raw_modified': stats.st_mtime,  # Raw timestamp for sorting
                        'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')  # Formatted date for display
                    })

            files_html = '\n'.join([
                f'''<tr data-name="{f['name']}" data-size="{f['raw_size']}" data-date="{f['raw_modified']}">
                    <td><a href="{f['name']}" class="file-link">{f['name']}</a></td>
                    <td class="size-cell">{f['size']}</td>
                    <td class="date-cell">{f['modified']}</td>
                </tr>''' for f in files
            ])

            html = f'''
            <html>
            <head>
                <title>File Transfer Server</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                        color: #333;
                    }}
                    .container {{
                        max-width: 1000px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h2 {{
                        margin-top: 0;
                        color: #2c3e50;
                        font-weight: 500;
                    }}
                    .upload-form {{
                        margin: 20px 0;
                        padding: 20px;
                        background: #f8f9fa;
                        border-radius: 8px;
                        border: 2px dashed #dee2e6;
                    }}
                    .upload-form h3 {{
                        margin-top: 0;
                        color: #495057;
                    }}
                    input[type="file"] {{
                        display: block;
                        margin: 10px 0;
                    }}
                    input[type="submit"] {{
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                    }}
                    input[type="submit"]:hover {{
                        background: #0056b3;
                    }}
                    .file-list {{
                        margin-top: 30px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 10px;
                    }}
                    th, td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #dee2e6;
                    }}
                    th {{
                        background: #f8f9fa;
                        font-weight: 500;
                        color: #495057;
                        cursor: pointer;
                        user-select: none;
                        position: relative;
                    }}
                    th:hover {{
                        background: #e9ecef;
                    }}
                    th.sorted::after {{
                        content: "";
                        display: inline-block;
                        width: 0;
                        height: 0;
                        margin-left: 8px;
                        vertical-align: middle;
                        border-left: 4px solid transparent;
                        border-right: 4px solid transparent;
                    }}
                    th.sorted.asc::after {{
                        border-bottom: 4px solid #495057;
                    }}
                    th.sorted.desc::after {{
                        border-top: 4px solid #495057;
                    }}
                    tr:hover {{
                        background: #f8f9fa;
                    }}
                    .file-link {{
                        color: #007bff;
                        text-decoration: none;
                    }}
                    .file-link:hover {{
                        text-decoration: underline;
                    }}
                    .size-cell, .date-cell {{
                        color: #6c757d;
                        font-size: 0.9em;
                    }}
                    .server-info {{
                        margin-top: 20px;
                        font-size: 0.85em;
                        color: #6c757d;
                    }}
                </style>
                <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        const table = document.querySelector('table');
                        const tbody = table.querySelector('tbody');
                        const headers = table.querySelectorAll('th');
                        let currentSort = {{ column: 'name', direction: 'asc' }};

                        // Function to sort table rows
                        function sortTable(column) {{
                            const rows = Array.from(tbody.querySelectorAll('tr'));
                            const dataKey = {{'name': 'name', 'size': 'size', 'date': 'date'}}[column];
                            
                            // If clicking the same column, reverse direction
                            if (currentSort.column === column) {{
                                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
                            }} else {{
                                currentSort = {{ column, direction: 'asc' }};
                            }}

                            // Update header classes
                            headers.forEach(header => {{
                                header.classList.remove('sorted', 'asc', 'desc');
                                if (header.dataset.column === column) {{
                                    header.classList.add('sorted', currentSort.direction);
                                }}
                            }});

                            // Sort rows
                            rows.sort((a, b) => {{
                                let aValue = a.dataset[dataKey];
                                let bValue = b.dataset[dataKey];
                                
                                // Convert to numbers for size and date comparison
                                if (dataKey !== 'name') {{
                                    aValue = Number(aValue);
                                    bValue = Number(bValue);
                                }}
                                
                                if (aValue < bValue) return currentSort.direction === 'asc' ? -1 : 1;
                                if (aValue > bValue) return currentSort.direction === 'asc' ? 1 : -1;
                                return 0;
                            }});

                            // Reorder DOM
                            rows.forEach(row => tbody.appendChild(row));
                        }}

                        // Add click handlers to headers
                        headers.forEach(header => {{
                            header.addEventListener('click', () => sortTable(header.dataset.column));
                        }});

                        // Initial sort
                        sortTable('name');
                    }});
                </script>
            </head>
            <body>
                <div class="container">
                    <h2>File Transfer Server</h2>
                    <div class="upload-form">
                        <h3>Upload File</h3>
                        <form enctype="multipart/form-data" method="post">
                            <input type="file" name="file" required>
                            <input type="submit" value="Upload">
                        </form>
                    </div>
                    <div class="file-list">
                        <h3>Available Files</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th data-column="name" class="sorted asc">Filename</th>
                                    <th data-column="size">Size</th>
                                    <th data-column="date">Last Modified</th>
                                </tr>
                            </thead>
                            <tbody>
                                {files_html}
                            </tbody>
                        </table>
                    </div>
                    <div class="server-info">
                        <p>Server started at: {self.server.start_time}</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            self.wfile.write(html.encode())
        else:
            # Serve the requested file
            try:
                filepath = os.path.join('.', self.path.lstrip('/'))
                with open(filepath, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
                    self.end_headers()
                    self.wfile.write(f.read())
            except:
                self.send_error(404, 'File not found')

    def parse_multipart(self):
        content_type = self.headers['Content-Type']

        if not content_type:
            return None

        # Get the boundary from content-type
        boundary = content_type.split('=')[1].encode()
        remainbytes = int(self.headers['Content-Length'])

        # Read the initial headers
        line = self.rfile.readline()
        remainbytes -= len(line)

        if not boundary in line:
            return None

        # Read the part headers
        line = self.rfile.readline()
        remainbytes -= len(line)

        # Parse the part headers
        parser = BytesParser()
        headers = parser.parsebytes(line + b'\r\n')

        # Get the filename from Content-Disposition
        content_disp = headers.get('Content-Disposition', '')
        if not content_disp:
            return None

        # Parse the filename
        for part in content_disp.split(';'):
            part = part.strip()
            if part.startswith('filename='):
                filename = part[9:].strip('"')
                return filename, remainbytes

        return None

    def do_POST(self):
        # Handle file upload
        try:
            result = self.parse_multipart()
            if not result:
                self.send_error(400, 'Invalid form data')
                return

            filename, remainbytes = result

            # Read the file content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                while remainbytes > 0:
                    line = self.rfile.readline()
                    remainbytes -= len(line)
                    if b'--' + result[0].encode() in line:
                        break
                    temp_file.write(line)

                # Move temp file to final location
                temp_file.close()
                os.rename(temp_file.name, filename)

            # Redirect back to main page
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

        except Exception as e:
            print(f"Upload error: {str(e)}")
            self.send_error(500, 'Upload failed')

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
    httpd.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    local_ip = get_local_ip()

    print(f"\nFile Transfer Server Running")
    print(f"==============================")
    print(f"Local Access: http://{local_ip}:{port}")
    print(f"Local Files: {os.getcwd()}")
    print(f"\nPress Ctrl+C to stop the server\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple HTTP Server with Upload capability')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    args = parser.parse_args()

    run_server(args.port)