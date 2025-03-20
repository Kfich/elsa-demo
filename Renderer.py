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
