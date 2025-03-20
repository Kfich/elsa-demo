#!/usr/bin/env python3
import socket
import threading
import time

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


class TextBuffer:
    def __init__(self):
        self.lines = [""]
        self.cursor_row = 0
        self.cursor_col = 0
        self.char_width = 8  # As per README
        self.char_height = 14  # As per README
        self.scroll_y = 0
        self.selection_start = None
        self.selection_end = None
        
    def insert_char(self, char):
        # Remove any selected text if there's a selection
        self.delete_selection()
        
        # Handle newline
        if char == '\n':
            # Split the current line at cursor
            current_line = self.lines[self.cursor_row]
            before_cursor = current_line[:self.cursor_col]
            after_cursor = current_line[self.cursor_col:]
            
            # Update current line to be text before cursor
            self.lines[self.cursor_row] = before_cursor
            
            # Insert new line with text after cursor
            self.lines.insert(self.cursor_row + 1, after_cursor)
            
            # Move cursor to beginning of new line
            self.cursor_row += 1
            self.cursor_col = 0
        else:
            # Insert character at cursor position
            current_line = self.lines[self.cursor_row]
            new_line = current_line[:self.cursor_col] + char + current_line[self.cursor_col:]
            self.lines[self.cursor_row] = new_line
            self.cursor_col += 1
    
    def delete_char(self):
        # If there's a selection, delete it
        if self.has_selection():
            self.delete_selection()
            return
            
        if self.cursor_col > 0:
            # Delete character before cursor
            current_line = self.lines[self.cursor_row]
            new_line = current_line[:self.cursor_col-1] + current_line[self.cursor_col:]
            self.lines[self.cursor_row] = new_line
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            # At beginning of line, join with previous line
            current_line = self.lines[self.cursor_row]
            prev_line = self.lines[self.cursor_row - 1]
            
            # Set cursor to end of previous line
            self.cursor_col = len(prev_line)
            
            # Join lines
            self.lines[self.cursor_row - 1] = prev_line + current_line
            
            # Remove current line
            self.lines.pop(self.cursor_row)
            
            # Move cursor up
            self.cursor_row -= 1
    
    def move_cursor_left(self, select=False):
        # Update selection if needed
        if select:
            if not self.has_selection():
                self.selection_start = (self.cursor_row, self.cursor_col)
        else:
            self.clear_selection()
            
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            self.cursor_row -= 1
            self.cursor_col = len(self.lines[self.cursor_row])
            
        # Update selection end if selecting
        if select:
            self.selection_end = (self.cursor_row, self.cursor_col)
    
    def move_cursor_right(self, select=False):
        # Update selection if needed
        if select:
            if not self.has_selection():
                self.selection_start = (self.cursor_row, self.cursor_col)
        else:
            self.clear_selection()
            
        if self.cursor_col < len(self.lines[self.cursor_row]):
            self.cursor_col += 1
        elif self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            self.cursor_col = 0
            
        # Update selection end if selecting
        if select:
            self.selection_end = (self.cursor_row, self.cursor_col)
    
    def move_cursor_up(self, select=False):
        # Update selection if needed
        if select:
            if not self.has_selection():
                self.selection_start = (self.cursor_row, self.cursor_col)
        else:
            self.clear_selection()
            
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Adjust column if new line is shorter
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
            
        # Update selection end if selecting
        if select:
            self.selection_end = (self.cursor_row, self.cursor_col)
    
    def move_cursor_down(self, select=False):
        # Update selection if needed
        if select:
            if not self.has_selection():
                self.selection_start = (self.cursor_row, self.cursor_col)
        else:
            self.clear_selection()
            
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            # Adjust column if new line is shorter
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
            
        # Update selection end if selecting
        if select:
            self.selection_end = (self.cursor_row, self.cursor_col)
    
    def move_cursor_to_position(self, row, col, select=False):
        # Validate position
        row = max(0, min(row, len(self.lines) - 1))
        col = max(0, min(col, len(self.lines[row])))
        
        # Update selection if needed
        if select:
            if not self.has_selection():
                self.selection_start = (self.cursor_row, self.cursor_col)
        else:
            self.clear_selection()
        
        # Move cursor
        self.cursor_row = row
        self.cursor_col = col
        
        # Update selection end if selecting
        if select:
            self.selection_end = (self.cursor_row, self.cursor_col)
    
    def has_selection(self):
        return self.selection_start is not None and self.selection_end is not None
    
    def clear_selection(self):
        self.selection_start = None
        self.selection_end = None
    
    def get_ordered_selection(self):
        if not self.has_selection():
            return None
            
        start_row, start_col = self.selection_start
        end_row, end_col = self.selection_end
        
        # Make sure start is before end
        if start_row > end_row or (start_row == end_row and start_col > end_col):
            return (end_row, end_col, start_row, start_col)
        else:
            return (start_row, start_col, end_row, end_col)
    
    def delete_selection(self):
        if not self.has_selection():
            return
            
        start_row, start_col, end_row, end_col = self.get_ordered_selection()
        
        # If selection is on same line
        if start_row == end_row:
            line = self.lines[start_row]
            self.lines[start_row] = line[:start_col] + line[end_col:]
            self.cursor_row = start_row
            self.cursor_col = start_col
        else:
            # Handle multi-line selection
            start_line = self.lines[start_row]
            end_line = self.lines[end_row]
            
            # Create new line that joins start and end
            new_line = start_line[:start_col] + end_line[end_col:]
            self.lines[start_row] = new_line
            
            # Remove all lines in between
            for _ in range(end_row - start_row):
                self.lines.pop(start_row + 1)
            
            # Set cursor position
            self.cursor_row = start_row
            self.cursor_col = start_col
        
        # Clear selection
        self.clear_selection()
    
    def get_selected_text(self):
        if not self.has_selection():
            return ""
            
        start_row, start_col, end_row, end_col = self.get_ordered_selection()
        
        if start_row == end_row:
            return self.lines[start_row][start_col:end_col]
        else:
            result = []
            # First line
            result.append(self.lines[start_row][start_col:])
            
            # Middle lines
            for row in range(start_row + 1, end_row):
                result.append(self.lines[row])
            
            # Last line
            result.append(self.lines[end_row][:end_col])
            
            return '\n'.join(result)
    
    def insert_text(self, text):
        # Remove any selected text first
        self.delete_selection()
        
        # Split text into lines
        text_lines = text.split('\n')
        
        if len(text_lines) == 1:
            # Simple case - just insert the text
            current_line = self.lines[self.cursor_row]
            new_line = current_line[:self.cursor_col] + text_lines[0] + current_line[self.cursor_col:]
            self.lines[self.cursor_row] = new_line
            self.cursor_col += len(text_lines[0])
        else:
            # Complex case - handle multiple lines
            current_line = self.lines[self.cursor_row]
            before_cursor = current_line[:self.cursor_col]
            after_cursor = current_line[self.cursor_col:]
            
            # First line combines with text before cursor
            self.lines[self.cursor_row] = before_cursor + text_lines[0]
            
            # Middle lines
            for i in range(1, len(text_lines) - 1):
                self.lines.insert(self.cursor_row + i, text_lines[i])
            
            # Last line combines with text after cursor
            last_index = len(text_lines) - 1
            self.lines.insert(self.cursor_row + last_index, text_lines[last_index] + after_cursor)
            
            # Update cursor position
            self.cursor_row += last_index
            self.cursor_col = len(text_lines[last_index])
    
    def ensure_cursor_visible(self, visible_lines):
        # Scroll up if cursor is above visible area
        if self.cursor_row < self.scroll_y:
            self.scroll_y = self.cursor_row
        
        # Scroll down if cursor is below visible area
        if self.cursor_row >= self.scroll_y + visible_lines:
            self.scroll_y = max(0, self.cursor_row - visible_lines + 1)


class Renderer:
    def __init__(self, client, text_buffer):
        self.client = client
        self.buffer = text_buffer
        self.canvas_width = 800  # Default width
        self.canvas_height = 600  # Default height
        self.cursor_blink = True
        self.cursor_blink_timer = None
        self.status_bar_height = 20
        self.line_numbers = True
        self.gutter_width = 40  # Width for line numbers
        self.show_legend = False  # Toggle for command legend
        self.legend_width = 250   # Width of the legend box
        self.legend_height = 210  # Height of the legend box
        
    def render(self):
        # Clear the screen
        self.client.clear_screen()
        
        # Calculate visible lines based on scroll position
        content_height = self.canvas_height - self.status_bar_height
        visible_lines_count = content_height // self.buffer.char_height
        
        # Make sure cursor is visible
        self.buffer.ensure_cursor_visible(visible_lines_count)
        
        start_line = self.buffer.scroll_y
        end_line = min(start_line + visible_lines_count, len(self.buffer.lines))
        
        # Draw gutter background
        if self.line_numbers:
            self.client.draw_rect(0, 0, self.gutter_width, content_height, "#F0F0F0")
            # Draw separator line
            self.client.draw_rect(self.gutter_width - 1, 0, 1, content_height, "#D0D0D0")
        
        # Get content x offset (accounting for gutter)
        content_x = self.gutter_width if self.line_numbers else 0
        
        # Get ordered selection if exists
        selection_info = None
        if self.buffer.has_selection():
            selection_info = self.buffer.get_ordered_selection()
        
        # Draw visible text lines
        for i in range(start_line, end_line):
            y = (i - start_line) * self.buffer.char_height
            
            # Draw line number
            if self.line_numbers:
                line_num = str(i + 1).rjust(4)
                self.client.draw_text(5, y, "#808080", line_num)
            
            # Draw line highlight for cursor line
            if i == self.buffer.cursor_row:
                self.client.draw_rect(
                    content_x, y, 
                    self.canvas_width - content_x, self.buffer.char_height, 
                    "#F8F8F8"
                )
            
            # Draw line text
            self.client.draw_text(content_x, y, "#000000", self.buffer.lines[i])
            
            # Draw selection highlight if exists
            if selection_info:
                start_row, start_col, end_row, end_col = selection_info
                
                if start_row <= i <= end_row:
                    # Calculate highlight position
                    highlight_start_x = content_x
                    highlight_end_x = content_x + len(self.buffer.lines[i]) * self.buffer.char_width
                    
                    if i == start_row:
                        highlight_start_x = content_x + start_col * self.buffer.char_width
                    if i == end_row:
                        highlight_end_x = content_x + end_col * self.buffer.char_width
                    
                    # Draw selection highlight
                    if highlight_end_x > highlight_start_x:
                        self.client.draw_rect(
                            highlight_start_x, y,
                            highlight_end_x - highlight_start_x, self.buffer.char_height,
                            "#ADD8E6"  # Light blue
                        )
        
        # Draw cursor if visible and in blink state
        if self.cursor_blink and start_line <= self.buffer.cursor_row < end_line:
            cursor_x = content_x + self.buffer.cursor_col * self.buffer.char_width
            cursor_y = (self.buffer.cursor_row - start_line) * self.buffer.char_height
            self.client.draw_rect(cursor_x, cursor_y, 2, self.buffer.char_height, "#0000FF")
        
        # Draw command legend if enabled
        if self.show_legend:
            self._draw_command_legend()
        
        # Draw status bar
        status_y = self.canvas_height - self.status_bar_height
        self.client.draw_rect(0, status_y, self.canvas_width, self.status_bar_height, "#2C3E50")
        
        # Draw status text
        position_text = f"Line: {self.buffer.cursor_row+1}, Col: {self.buffer.cursor_col+1}"
        line_count_text = f"Total Lines: {len(self.buffer.lines)}"
        
        # Left-aligned position info
        self.client.draw_text(10, status_y + 3, "#FFFFFF", position_text)
        
        # Right-aligned line count
        right_text_x = self.canvas_width - (len(line_count_text) * self.buffer.char_width) - 10
        self.client.draw_text(right_text_x, status_y + 3, "#FFFFFF", line_count_text)
        
        # Center editor name with legend toggle hint
        editor_name = "Canvas Text Editor (Press Ctrl+H for help)"
        center_x = (self.canvas_width - len(editor_name) * self.buffer.char_width) // 2
        self.client.draw_text(center_x, status_y + 3, "#FFFFFF", editor_name)
        
    def _draw_command_legend(self):
        """Draw a command reference legend in the bottom right corner"""
        # Calculate legend position (bottom right)
        legend_x = self.canvas_width - self.legend_width - 20
        legend_y = self.canvas_height - self.legend_height - self.status_bar_height - 20
        
        # Draw semi-transparent background
        self.client.draw_rect(legend_x, legend_y, self.legend_width, self.legend_height, "#F8F8F8")
        
        # Draw border
        border_color = "#2C3E50"
        # Top border
        self.client.draw_rect(legend_x, legend_y, self.legend_width, 1, border_color)
        # Left border
        self.client.draw_rect(legend_x, legend_y, 1, self.legend_height, border_color)
        # Right border
        self.client.draw_rect(legend_x + self.legend_width - 1, legend_y, 1, self.legend_height, border_color)
        # Bottom border
        self.client.draw_rect(legend_x, legend_y + self.legend_height - 1, self.legend_width, 1, border_color)
        
        # Draw title
        title = "Keyboard Shortcuts"
        title_x = legend_x + (self.legend_width - len(title) * self.buffer.char_width) // 2
        self.client.draw_text(title_x, legend_y + 5, "#000000", title)
        
        # Draw horizontal separator
        self.client.draw_rect(legend_x + 10, legend_y + 25, self.legend_width - 20, 1, "#AAAAAA")
        
        # Draw command shortcuts
        commands = [
            ("Ctrl+C", "Copy"),
            ("Ctrl+X", "Cut"),
            ("Ctrl+V", "Paste"),
            ("Ctrl+A", "Select All"),
            ("Ctrl+N", "New Document"),
            ("Ctrl+L", "Toggle Line Numbers"),
            ("Ctrl+H", "Toggle This Help"),
            ("Arrow Keys", "Navigation"),
            ("Shift+Arrows", "Select Text"),
            ("Home/End", "Start/End of Line"),
            ("Tab", "Insert 4 spaces"),
            ("Escape", "Clear Selection")
        ]
        
        y_offset = legend_y + 35
        for shortcut, description in commands:
            # Draw shortcut (left column)
            self.client.draw_text(legend_x + 15, y_offset, "#2C3E50", shortcut)
            
            # Draw description (right column)
            self.client.draw_text(legend_x + 115, y_offset, "#000000", description)
            
            y_offset += 15
        
    def toggle_cursor_blink(self):
        self.cursor_blink = not self.cursor_blink
        self.render()
        
    def start_cursor_blink(self):
        if self.cursor_blink_timer:
            self.cursor_blink_timer.cancel()
        
        # Toggle cursor every 500ms
        self.cursor_blink_timer = threading.Timer(0.5, self.start_cursor_blink)
        self.cursor_blink_timer.daemon = True
        self.cursor_blink_timer.start()
        
        self.toggle_cursor_blink()
        
    def stop_cursor_blink(self):
        if self.cursor_blink_timer:
            self.cursor_blink_timer.cancel()
            self.cursor_blink_timer = None
            
    def toggle_line_numbers(self):
        self.line_numbers = not self.line_numbers
        self.render()
        
    def toggle_legend(self):
        self.show_legend = not self.show_legend
        self.render()


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