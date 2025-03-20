import threading

class Renderer:
    def __init__(self, client, text_buffer):
        self.client = client
        self.buffer = text_buffer
        self.canvas_width = 800  # Default width
        self.canvas_height = 600  # Default height
        self.cursor_blink = True
        self.cursor_blink_timer = None
        
    def render(self):
        # Clear the screen
        self.client.clear_screen()
        
        # Calculate visible lines based on scroll position
        visible_lines_count = self.canvas_height // self.buffer.char_height
        start_line = self.buffer.scroll_y
        end_line = min(start_line + visible_lines_count, len(self.buffer.lines))
        
        # Draw visible text lines
        for i in range(start_line, end_line):
            y = (i - start_line) * self.buffer.char_height
            self.client.draw_text(0, y, "#000000", self.buffer.lines[i])
        
        # Draw cursor if visible and in blink state
        if self.cursor_blink and start_line <= self.buffer.cursor_row < end_line:
            cursor_x = self.buffer.cursor_col * self.buffer.char_width
            cursor_y = (self.buffer.cursor_row - start_line) * self.buffer.char_height
            self.client.draw_rect(cursor_x, cursor_y, 2, self.buffer.char_height, "#000000")
        
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