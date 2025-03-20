
### TextBuffer.py ###
# This module defines a TextBuffer class that manages the text content,
# cursor position, and text selection for a text editor. It provides methods
# for inserting, deleting, and moving text, as well as handling cursor
# visibility and text selection.

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