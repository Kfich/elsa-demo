import time
from TextEditor import TextEditor
import argparse



def main():    
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
    
    editor = TextEditor(args.host, args.port)  # Ensure TextEditor is a class
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
    main()#!/usr/bin/env python3