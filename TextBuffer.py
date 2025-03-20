class TextBuffer:
    def __init__(self):
        self.lines = [""]
        self.cursor_row = 0
        self.cursor_col = 0
        self.char_width = 8  # As per README
        self.char_height = 14  # As per README
        self.scroll_y = 0
        
    def insert_char(self, char):
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
    
    def move_cursor_left(self):
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            self.cursor_row -= 1
            self.cursor_col = len(self.lines[self.cursor_row])
    
    def move_cursor_right(self):
        if self.cursor_col < len(self.lines[self.cursor_row]):
            self.cursor_col += 1
        elif self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            self.cursor_col = 0
    
    def move_cursor_up(self):
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Adjust column if new line is shorter
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
    
    def move_cursor_down(self):
        if self.cursor_row < len(self.lines) - 1:
            self.cursor_row += 1
            # Adjust column if new line is shorter
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))