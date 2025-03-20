#!/usr/bin/env python3
import socket
import threading
import time
import TextEditor

### TextEditorClient.py ###
# This module defines a TextEditorClient class that connects to a socket server
# for a text editor application. It handles sending commands to the server and
# receiving events from it. The client can draw on a canvas, handle keyboard
# events, and manage a text buffer. 

class TextEditorClient:
    def __init__(self, host='localhost', port=5005):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.event_handlers = {
            'resize': [],
            'mousedown': [],
            'mouseup': [],
            'mousemove': [],
            'keydown': [],
            'keyup': []
        }

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Start listening for events
            self.listen_thread = threading.Thread(target=self.listen_for_events)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        if self.connected:
            self.connected = False
            self.socket.close()

    def send_command(self, command):
        if not self.connected:
            return False
        
        if not command.endswith('\n'):
            command += '\n'
        
        try:
            self.socket.sendall(command.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
            return False

    def listen_for_events(self):
        buffer = ""
        
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    self.connected = False
                    break
                
                buffer += data
                
                # Process complete events (ones that end with newline)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_event(line)
                    
            except Exception as e:
                print(f"Receive error: {e}")
                self.connected = False
                break

    def process_event(self, event_str):
        parts = event_str.split(',')
        if len(parts) >= 1:
            event_type = parts[0]
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(parts)

    def on(self, event_type, handler):
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    # Canvas API commands
    def draw_rect(self, x, y, width, height, color):
        return self.send_command(f"rect,{x},{y},{width},{height},{color}")

    def draw_text(self, x, y, color, text):
        return self.send_command(f"text,{x},{y},{color},{text}")

    def clear_screen(self):
        return self.send_command("clear")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Text Editor using Canvas Socket API')
    parser.add_argument('--host', default='localhost', help='Canvas API host')
    parser.add_argument('--port', type=int, default=5005, help='Canvas API port')
    
    args = parser.parse_args()
    
    print(f"Starting Text Editor - connecting to {args.host}:{args.port}")
    print("Keyboard shortcuts:")
    print("  Ctrl+C - Copy")
    print("  Ctrl+X - Cut")
    print("  Ctrl+V - Paste")
    print("  Ctrl+A - Select All")
    print("  Ctrl+N - New File")
    print("  Ctrl+L - Toggle Line Numbers")
    print("  Ctrl+H - Toggle Command Legend")
    
    editor = TextEditor(args.host, args.port)
    if editor.start():
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            editor.client.disconnect()
    else:
        print("Failed to start editor. Is the socket_canvas.py running?")


if __name__ == "__main__":
    main()