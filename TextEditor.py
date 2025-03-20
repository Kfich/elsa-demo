# TextEditor.py
# A simple text editor that connects to a canvas and handles user input
from TextEditorClient import TextEditorClient
from TextBuffer import TextBuffer
from Renderer import Renderer

class TextEditor:
    def __init__(self):
        self.client = TextEditorClient()
        self.buffer = TextBuffer()
        self.renderer = Renderer(self.client, self.buffer)
        
    def start(self):
        if not self.client.connect():
            print("Failed to connect to canvas!")
            return False
        
        # Register event handlers
        self.client.on('resize', self.handle_resize)
        self.client.on('keydown', self.handle_keydown)
        self.client.on('mousedown', self.handle_mousedown)
        
        # Start rendering
        self.renderer.start_cursor_blink()
        self.renderer.render()
        
        print("Text editor started!")
        return True
    
    def handle_resize(self, event_parts):
        if len(event_parts) >= 3:
            width = int(event_parts[1])
            height = int(event_parts[2])
            self.renderer.canvas_width = width
            self.renderer.canvas_height = height
            self.renderer.render()
    
    def handle_keydown(self, event_parts):
        if len(event_parts) >= 2:
            key = event_parts[1]
            
            # Handle special keys
            if key == "BackSpace":
                self.buffer.delete_char()
            elif key == "Left":
                self.buffer.move_cursor_left()
            elif key == "Right":
                self.buffer.move_cursor_right()
            elif key == "Up":
                self.buffer.move_cursor_up()
            elif key == "Down":
                self.buffer.move_cursor_down()
            elif key == "Return":
                self.buffer.insert_char('\n')
            elif key == "Tab":
                # Insert 4 spaces for tab
                for _ in range(4):
                    self.buffer.insert_char(' ')
            elif len(key) == 1:  # Regular character
                self.buffer.insert_char(key)
            
            # Re-render after any key action
            self.renderer.render()
    
    def handle_mousedown(self, event_parts):
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Calculate row and column from click coordinates
            row = self.buffer.scroll_y + (y // self.buffer.char_height)
            col = x // self.buffer.char_width
            
            # Ensure valid row and column
            if 0 <= row < len(self.buffer.lines):
                self.buffer.cursor_row = row
                self.buffer.cursor_col = min(col, len(self.buffer.lines[row]))
                self.renderer.render()