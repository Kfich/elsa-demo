
from TextBuffer import TextBuffer
from Renderer import Renderer
from TextEditorClient import TextEditorClient

### TextEditor ###
# This class handles user input, text manipulation, and rendering of the text
# It communicates with a client to draw on a canvas and uses a text buffer
# to manage the text content and cursor position.

class TextEditor:
    def __init__(self, host='localhost', port=5005):
        self.client = TextEditorClient(host, port)
        self.buffer = TextBuffer()
        self.renderer = Renderer(self.client, self.buffer)
        self.clipboard = ""
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.modified = False
        self.filename = "untitled.txt"
        
    def start(self):
        if not self.client.connect():
            print("Failed to connect to canvas!")
            return False
        
        # Register event handlers
        self.client.on('resize', self.handle_resize)
        self.client.on('keydown', self.handle_keydown)
        self.client.on('keyup', self.handle_keyup)
        self.client.on('mousedown', self.handle_mousedown)
        self.client.on('mousemove', self.handle_mousemove)
        self.client.on('mouseup', self.handle_mouseup)
        
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
            
            # Track modifier keys
            if key == "LeftShift" or key == "RightShift":
                self.shift_pressed = True
                return
            elif key == "LeftControl" or key == "RightControl":
                self.ctrl_pressed = True
                return
                
            # Handle keyboard shortcuts with Ctrl key
            if self.ctrl_pressed:
                if key == "c":  # Copy
                    if self.buffer.has_selection():
                        self.clipboard = self.buffer.get_selected_text()
                elif key == "x":  # Cut
                    if self.buffer.has_selection():
                        self.clipboard = self.buffer.get_selected_text()
                        self.buffer.delete_selection()
                        self.modified = True
                elif key == "v":  # Paste
                    if self.clipboard:
                        self.buffer.insert_text(self.clipboard)
                        self.modified = True
                elif key == "a":  # Select all
                    self.buffer.selection_start = (0, 0)
                    last_row = len(self.buffer.lines) - 1
                    last_col = len(self.buffer.lines[last_row])
                    self.buffer.selection_end = (last_row, last_col)
                    self.buffer.cursor_row = last_row
                    self.buffer.cursor_col = last_col
                elif key == "z":  # Undo (placeholder for future implementation)
                    pass
                elif key == "y":  # Redo (placeholder for future implementation)
                    pass
                elif key == "s":  # Save (placeholder for future implementation)
                    print(f"Would save file as {self.filename}")
                    self.modified = False
                elif key == "n":  # New file
                    self.buffer.lines = [""]
                    self.buffer.cursor_row = 0
                    self.buffer.cursor_col = 0
                    self.buffer.clear_selection()
                    self.buffer.scroll_y = 0
                    self.modified = False
                    self.filename = "untitled.txt"
                elif key == "l":  # Toggle line numbers
                    self.renderer.toggle_line_numbers()
                elif key == "h":  # Toggle help/legend
                    self.renderer.toggle_legend()
            else:
                # Handle navigation keys
                if key == "BackSpace":
                    self.buffer.delete_char()
                    self.modified = True
                elif key == "Delete":
                    # If there's a selection, delete it
                    if self.buffer.has_selection():
                        self.buffer.delete_selection()
                    # Otherwise delete character after cursor
                    elif self.buffer.cursor_col < len(self.buffer.lines[self.buffer.cursor_row]):
                        # Move cursor right and then delete backwards
                        self.buffer.move_cursor_right()
                        self.buffer.delete_char()
                    # If at end of line but not last line, join with next line
                    elif self.buffer.cursor_row < len(self.buffer.lines) - 1:
                        next_line = self.buffer.lines[self.buffer.cursor_row + 1]
                        self.buffer.lines[self.buffer.cursor_row] += next_line
                        self.buffer.lines.pop(self.buffer.cursor_row + 1)
                    self.modified = True
                elif key == "Left":
                    self.buffer.move_cursor_left(self.shift_pressed)
                elif key == "Right":
                    self.buffer.move_cursor_right(self.shift_pressed)
                elif key == "Up":
                    self.buffer.move_cursor_up(self.shift_pressed)
                elif key == "Down":
                    self.buffer.move_cursor_down(self.shift_pressed)
                elif key == "Home":
                    # Move to beginning of line
                    self.buffer.cursor_col = 0
                    if self.shift_pressed:
                        if not self.buffer.has_selection():
                            self.buffer.selection_start = (self.buffer.cursor_row, self.buffer.cursor_col)
                        self.buffer.selection_end = (self.buffer.cursor_row, 0)
                elif key == "End":
                    # Move to end of line
                    self.buffer.cursor_col = len(self.buffer.lines[self.buffer.cursor_row])
                    if self.shift_pressed:
                        if not self.buffer.has_selection():
                            self.buffer.selection_start = (self.buffer.cursor_row, self.buffer.cursor_col)
                        self.buffer.selection_end = (self.buffer.cursor_row, self.buffer.cursor_col)
                elif key == "Return":
                    self.buffer.insert_char('\n')
                    self.modified = True
                elif key == "Tab":
                    # Insert 4 spaces for tab
                    for _ in range(4):
                        self.buffer.insert_char(' ')
                    self.modified = True
                elif key == "Escape":
                    # Clear selection
                    self.buffer.clear_selection()
                elif len(key) == 1:  # Regular character
                    self.buffer.insert_char(key)
                    self.modified = True
            
            # Re-render after any key action
            self.renderer.render()
    
    def handle_keyup(self, event_parts):
        if len(event_parts) >= 2:
            key = event_parts[1]
            
            # Track modifier keys
            if key == "LeftShift" or key == "RightShift":
                self.shift_pressed = False
            elif key == "LeftControl" or key == "RightControl":
                self.ctrl_pressed = False
    
    def handle_mousedown(self, event_parts):
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Check if click is in the text content area
            content_x = self.renderer.gutter_width if self.renderer.line_numbers else 0
            if x < content_x:
                # Click in gutter - select whole line
                content_height = self.renderer.canvas_height - self.renderer.status_bar_height
                row = self.buffer.scroll_y + (y // self.buffer.char_height)
                
                if 0 <= row < len(self.buffer.lines):
                    # Select the entire line
                    self.buffer.selection_start = (row, 0)
                    self.buffer.selection_end = (row, len(self.buffer.lines[row]))
                    self.buffer.cursor_row = row
                    self.buffer.cursor_col = len(self.buffer.lines[row])
            else:
                # Click in text area - move cursor
                content_height = self.renderer.canvas_height - self.renderer.status_bar_height
                row = self.buffer.scroll_y + (y // self.buffer.char_height)
                col = (x - content_x) // self.buffer.char_width
                
                if 0 <= row < len(self.buffer.lines):
                    self.buffer.move_cursor_to_position(row, col, self.shift_pressed)
            
            self.renderer.render()
    
    def handle_mousemove(self, event_parts):
        if len(event_parts) >= 3 and self.buffer.has_selection():
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Calculate row and column from coordinates
            content_x = self.renderer.gutter_width if self.renderer.line_numbers else 0
            content_height = self.renderer.canvas_height - self.renderer.status_bar_height
            row = self.buffer.scroll_y + (y // self.buffer.char_height)
            col = max(0, (x - content_x) // self.buffer.char_width)
            
            # Ensure valid row and column
            if 0 <= row < len(self.buffer.lines):
                # Update cursor and selection end
                col = min(col, len(self.buffer.lines[row]))
                self.buffer.cursor_row = row
                self.buffer.cursor_col = col
                self.buffer.selection_end = (row, col)
                self.renderer.render()
    
    def handle_mouseup(self, event_parts):
        # Nothing special to do on mouse up for now
        pass
