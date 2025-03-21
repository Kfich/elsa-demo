import socket
import threading
import time
import json
import argparse

class ModernChessClient:
    def __init__(self, host='localhost', port=5005, server_host='localhost', server_port=5006, player_name=None):
        # Canvas connection
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
        # Server connection
        self.server_host = server_host
        self.server_port = server_port
        self.server_socket = None
        self.server_connected = False
        
        # Event handlers
        self.event_handlers = {
            'resize': [],
            'mousedown': [],
            'mouseup': [],
            'mousemove': [],
            'keydown': [],
            'keyup': []
        }
        
        # Game state
        self.canvas_width = 800
        self.canvas_height = 600
        self.board_size = 8  # 8x8 chess board
        self.square_size = 65  # Size of each square
        self.board_offset_x = 150  # Offset from left edge
        self.board_offset_y = 70   # Offset from top
        self.selected_piece = None  # Currently selected piece
        self.selected_square = None  # Currently selected square (row, col)
        self.board = self.create_initial_board()
        self.is_white = True  # Whether player is white or black
        self.players_turn = True  # Whether it's this player's turn
        self.player_name = player_name or f"Player-{int(time.time()) % 1000}"
        self.opponent_name = "Waiting for opponent..."
        self.game_id = None
        self.is_game_over = False
        self.winner = None
        self.message = "Connecting to server..."
        self.available_games = []  # For game lobby
        self.in_lobby = True  # Start in lobby mode
        self.in_game = False
        self.last_move = None
        self.hover_square = None  # Currently hovered square
        
        # Piece images (Unicode chess symbols)
        self.piece_chars = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',  # White pieces
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'   # Black pieces
        }
        
        # Modern color scheme
        self.colors = {
            # Board colors - soft elegant tones
            'light_square': '#E8EDF9',  # Light blue-gray
            'dark_square': '#B7C0D8',   # Medium blue-gray
            'selected': '#FFE2AD',      # Soft amber highlight
            'valid_move': '#AED581',    # Soft green
            'last_move': '#FFD180',     # Soft orange
            'hover': '#E1F5FE',         # Very light blue hover effect
            
            # Piece colors
            'black_piece': '#263238',   # Dark slate for black pieces
            'white_piece': '#FAFAFA',   # Off-white for white pieces
            
            # UI elements
            'board_border': '#90A4AE',  # Medium gray-blue border
            'background': '#ECEFF1',    # Light gray background
            'header_bg': '#37474F',     # Dark slate header
            'sidebar': '#CFD8DC',       # Light gray sidebar
            'text': '#263238',          # Dark text
            'light_text': '#ECEFF1',    # Light text for dark backgrounds
            'button': '#78909C',        # Blue-gray button
            'button_hover': '#546E7A',  # Darker blue-gray on hover
            'button_text': '#FFFFFF',   # White button text
            'status_good': '#66BB6A',   # Green status
            'status_warning': '#FFA726', # Orange warning
            'status_error': '#EF5350',  # Red error
            'divider': '#B0BEC5',       # Light divider color
            
            # Game lobby
            'lobby_header': '#455A64',  # Darker blue-gray for lobby header
            'game_item': '#ECEFF1',     # Light gray for game items
            'game_item_hover': '#CFD8DC' # Slightly darker on hover
        }
    
    def create_initial_board(self):
        """Create the initial chess board setup"""
        # Initialize empty board
        board = [[None for _ in range(8)] for _ in range(8)]
        
        # Place pawns
        for col in range(8):
            board[1][col] = 'p'  # Black pawns on row 1
            board[6][col] = 'P'  # White pawns on row 6
        
        # Place other pieces
        # Black pieces on top (rows 0)
        board[0][0] = board[0][7] = 'r'  # Rooks
        board[0][1] = board[0][6] = 'n'  # Knights
        board[0][2] = board[0][5] = 'b'  # Bishops
        board[0][3] = 'q'  # Queen
        board[0][4] = 'k'  # King
        
        # White pieces on bottom (row 7)
        board[7][0] = board[7][7] = 'R'  # Rooks
        board[7][1] = board[7][6] = 'N'  # Knights
        board[7][2] = board[7][5] = 'B'  # Bishops
        board[7][3] = 'Q'  # Queen
        board[7][4] = 'K'  # King
        
        return board
    
    def connect(self):
        """Connect to both canvas and server"""
        if not self.connect_to_canvas():
            return False
        
        if not self.connect_to_server():
            self.disconnect_from_canvas()
            return False
        
        return True
    
    def connect_to_canvas(self):
        """Connect to the canvas for rendering"""
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
            print(f"Canvas connection error: {e}")
            return False
    
    def connect_to_server(self):
        """Connect to the game server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_host, self.server_port))
            self.server_connected = True
            
            # Start listening for server messages
            self.server_listen_thread = threading.Thread(target=self.listen_for_server)
            self.server_listen_thread.daemon = True
            self.server_listen_thread.start()
            
            # Send player info to server
            self.send_to_server({
                'type': 'join_lobby',
                'name': self.player_name
            })
            
            self.message = "Connected. Waiting for opponent..."
            return True
        except Exception as e:
            print(f"Server connection error: {e}")
            self.message = f"Failed to connect to server: {e}"
            return False
    
    def disconnect(self):
        """Disconnect from both canvas and server"""
        self.disconnect_from_canvas()
        self.disconnect_from_server()
    
    def disconnect_from_canvas(self):
        """Disconnect from the canvas"""
        if self.connected:
            self.connected = False
            try:
                self.socket.close()
            except:
                pass
    
    def disconnect_from_server(self):
        """Disconnect from the game server"""
        if self.server_connected:
            self.server_connected = False
            try:
                self.server_socket.close()
            except:
                pass
    
    def send_command(self, command):
        """Send a command to the canvas"""
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
    
    def send_to_server(self, data):
        """Send data to the game server"""
        if not self.server_connected:
            return False
        
        try:
            message = json.dumps(data) + '\n'
            self.server_socket.sendall(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Server send error: {e}")
            self.server_connected = False
            return False
    
    def listen_for_events(self):
        """Listen for events from the canvas"""
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
    
    def listen_for_server(self):
        """Listen for messages from the game server"""
        buffer = ""
        
        while self.server_connected:
            try:
                data = self.server_socket.recv(4096).decode('utf-8')
                if not data:
                    self.server_connected = False
                    self.message = "Disconnected from server"
                    self.render()
                    break
                
                buffer += data
                
                # Process complete messages (ones that end with newline)
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    self.process_server_message(message)
                    
            except Exception as e:
                print(f"Server receive error: {e}")
                self.server_connected = False
                self.message = f"Server connection lost: {e}"
                self.render()
                break
    
    def process_event(self, event_str):
        """Process events from the canvas"""
        parts = event_str.split(',')
        if len(parts) >= 1:
            event_type = parts[0]
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    handler(parts)
    
    def process_server_message(self, message_str):
        """Process messages from the game server"""
        try:
            data = json.loads(message_str)
            message_type = data.get('type')
            
            if message_type == 'game_list':
                # Update list of available games
                self.available_games = data.get('games', [])
                self.render()
                
            elif message_type == 'game_created':
                # Game was created, we're waiting for opponent
                self.game_id = data.get('game_id')
                self.is_white = data.get('is_white', True)
                self.in_lobby = False
                self.in_game = True
                self.message = "Waiting for opponent to join..."
                self.render()
                
            elif message_type == 'game_joined':
                # We've joined a game
                self.game_id = data.get('game_id')
                self.is_white = data.get('is_white', False)
                self.opponent_name = data.get('opponent')
                self.in_lobby = False
                self.in_game = True
                self.players_turn = self.is_white  # White goes first
                self.message = "Game started! " + ("Your turn" if self.players_turn else "Opponent's turn")
                self.render()
                
            elif message_type == 'opponent_joined':
                # Opponent joined our game
                self.opponent_name = data.get('opponent')
                self.players_turn = self.is_white  # White goes first
                self.message = "Game started! " + ("Your turn" if self.players_turn else "Opponent's turn")
                self.render()
                
            elif message_type == 'move':
                # Opponent made a move
                move = data.get('move')
                if move:
                    # Make the immediate move
                    self.make_move(move['from_row'], move['from_col'], 
                                  move['to_row'], move['to_col'], is_opponent=True)
                    self.last_move = (move['from_row'], move['from_col'], 
                                     move['to_row'], move['to_col'])
                    self.players_turn = True
                    self.message = "Your turn"
                    self.render()
                    
            elif message_type == 'game_over':
                # Game is over
                self.is_game_over = True
                self.winner = data.get('winner')
                result = data.get('result', 'unknown')
                
                if self.winner:
                    if self.winner == self.player_name:
                        self.message = f"Game over - You won! ({result})"
                    else:
                        self.message = f"Game over - {self.winner} won. ({result})"
                else:
                    self.message = f"Game over - Draw. ({result})"
                
                self.render()
                
            elif message_type == 'error':
                # Error message from server
                self.message = f"Error: {data.get('message', 'Unknown error')}"
                self.render()
                
        except json.JSONDecodeError:
            print(f"Invalid JSON from server: {message_str}")
        except Exception as e:
            print(f"Error processing server message: {e}")
    
    def on(self, event_type, handler):
        """Register an event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    # Canvas API commands
    def draw_rect(self, x, y, width, height, color):
        """Draw a rectangle on the canvas"""
        return self.send_command(f"rect,{x},{y},{width},{height},{color}")
    
    def draw_text(self, x, y, color, text):
        """Draw text on the canvas"""
        return self.send_command(f"text,{x},{y},{color},{text}")
    
    def clear_screen(self):
        """Clear the canvas"""
        return self.send_command("clear")
    
    def get_board_position(self, x, y):
        """Convert screen coordinates to board position"""
        if (x < self.board_offset_x or x >= self.board_offset_x + self.square_size * 8 or
            y < self.board_offset_y or y >= self.board_offset_y + self.square_size * 8):
            return None  # Outside the board
        
        col = (x - self.board_offset_x) // self.square_size
        row = (y - self.board_offset_y) // self.square_size
        
        # Flip coordinates if playing as black
        if not self.is_white:
            row = 7 - row
            col = 7 - col
            
        return int(row), int(col)
    
    def get_screen_position(self, row, col):
        """Convert board position to screen coordinates"""
        # Flip coordinates if playing as black
        if not self.is_white:
            row = 7 - row
            col = 7 - col
            
        x = self.board_offset_x + col * self.square_size
        y = self.board_offset_y + row * self.square_size
        return x, y
    
    def is_valid_move(self, from_row, from_col, to_row, to_col):
        """Check if a move is valid"""
        # Basic validation - to be expanded with chess rules
        if from_row < 0 or from_row > 7 or from_col < 0 or from_col > 7:
            return False
        if to_row < 0 or to_row > 7 or to_col < 0 or to_col > 7:
            return False
        
        piece = self.board[from_row][from_col]
        if piece is None:
            return False  # No piece to move
            
        # Check if it's the player's piece
        if self.is_white and piece.islower():
            return False  # White player can't move black pieces
        if not self.is_white and piece.isupper():
            return False  # Black player can't move white pieces
            
        # Can't move to a square with same color piece
        target = self.board[to_row][to_col]
        if target is not None:
            if piece.isupper() and target.isupper():
                return False  # White can't capture white
            if piece.islower() and target.islower():
                return False  # Black can't capture black
                
        # Basic movement patterns
        piece_type = piece.upper()
        
        # Pawn movement
        if piece_type == 'P':
            return self.is_valid_pawn_move(piece, from_row, from_col, to_row, to_col)
        
        # Rook movement
        elif piece_type == 'R':
            return self.is_valid_rook_move(from_row, from_col, to_row, to_col)
        
        # Knight movement
        elif piece_type == 'N':
            return self.is_valid_knight_move(from_row, from_col, to_row, to_col)
        
        # Bishop movement
        elif piece_type == 'B':
            return self.is_valid_bishop_move(from_row, from_col, to_row, to_col)
        
        # Queen movement
        elif piece_type == 'Q':
            return (self.is_valid_rook_move(from_row, from_col, to_row, to_col) or 
                    self.is_valid_bishop_move(from_row, from_col, to_row, to_col))
        
        # King movement
        elif piece_type == 'K':
            return self.is_valid_king_move(from_row, from_col, to_row, to_col)
            
        return False  # Unknown piece type
    
    def is_valid_pawn_move(self, piece, from_row, from_col, to_row, to_col):
        """Check if a pawn move is valid"""
        # Direction based on color
        direction = -1 if piece.isupper() else 1  # White moves up (-1), black moves down (1)
        
        # Normal move forward
        if from_col == to_col and to_row == from_row + direction and self.board[to_row][to_col] is None:
            return True
            
        # First move can be 2 squares
        if (from_col == to_col and 
            ((piece.isupper() and from_row == 6 and to_row == 4) or 
             (piece.islower() and from_row == 1 and to_row == 3)) and
            self.board[from_row + direction][from_col] is None and
            self.board[to_row][to_col] is None):
            return True
            
        # Capture diagonally
        if abs(from_col - to_col) == 1 and to_row == from_row + direction:
            # There must be an opponent's piece to capture
            target = self.board[to_row][to_col]
            if target is not None:
                if piece.isupper() and target.islower():
                    return True  # White captures black
                if piece.islower() and target.isupper():
                    return True  # Black captures white
                    
        return False
    
    def is_valid_rook_move(self, from_row, from_col, to_row, to_col):
        """Check if a rook move is valid"""
        # Rook moves horizontally or vertically
        if from_row != to_row and from_col != to_col:
            return False
            
        # Check if path is clear
        if from_row == to_row:  # Horizontal move
            step = 1 if to_col > from_col else -1
            for col in range(from_col + step, to_col, step):
                if self.board[from_row][col] is not None:
                    return False  # Path is blocked
        else:  # Vertical move
            step = 1 if to_row > from_row else -1
            for row in range(from_row + step, to_row, step):
                if self.board[row][from_col] is not None:
                    return False  # Path is blocked
                    
        return True
    
    def is_valid_knight_move(self, from_row, from_col, to_row, to_col):
        """Check if a knight move is valid"""
        # Knight moves in L-shape: 2 squares in one direction and 1 in perpendicular
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
    
    def is_valid_bishop_move(self, from_row, from_col, to_row, to_col):
        """Check if a bishop move is valid"""
        # Bishop moves diagonally
        if abs(to_row - from_row) != abs(to_col - from_col):
            return False
            
        # Check if path is clear
        row_step = 1 if to_row > from_row else -1
        col_step = 1 if to_col > from_col else -1
        
        row = from_row + row_step
        col = from_col + col_step
        
        while row != to_row and col != to_col:
            if self.board[row][col] is not None:
                return False  # Path is blocked
            row += row_step
            col += col_step
                
        return True
    
    def is_valid_king_move(self, from_row, from_col, to_row, to_col):
        """Check if a king move is valid"""
        # King moves one square in any direction
        return abs(to_row - from_row) <= 1 and abs(to_col - from_col) <= 1
    
    def get_valid_moves(self, row, col):
        """Get all valid moves for a piece"""
        valid_moves = []
        for r in range(8):
            for c in range(8):
                if self.is_valid_move(row, col, r, c):
                    valid_moves.append((r, c))
        return valid_moves
    
    def make_move(self, from_row, from_col, to_row, to_col, is_opponent=False):
        """Make a chess move"""
        # Move the piece
        piece = self.board[from_row][from_col]
        self.board[from_row][from_col] = None
        self.board[to_row][to_col] = piece
        
        # Check for pawn promotion
        if piece.upper() == 'P' and (to_row == 0 or to_row == 7):
            # Promote to queen
            self.board[to_row][to_col] = 'Q' if piece.isupper() else 'q'
        
        if not is_opponent:
            # Send move to server
            self.send_to_server({
                'type': 'move',
                'game_id': self.game_id,
                'move': {
                    'from_row': from_row,
                    'from_col': from_col,
                    'to_row': to_row,
                    'to_col': to_col
                }
            })
            
            # Update game state
            self.players_turn = False
            self.message = "Waiting for opponent's move"
            self.last_move = (from_row, from_col, to_row, to_col)
    
    def handle_mousedown(self, event_parts):
        """Handle mouse down event"""
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Check if we're in game
            if self.in_game and not self.is_game_over:
                # Check if it's player's turn
                if self.players_turn:
                    # Get board position
                    pos = self.get_board_position(x, y)
                    if pos:
                        row, col = pos
                        
                        # If a piece is already selected, try to move it
                        if self.selected_square:
                            sel_row, sel_col = self.selected_square
                            
                            # If clicking the same square, deselect
                            if sel_row == row and sel_col == col:
                                self.selected_square = None
                            # If clicking a valid move square, make the move
                            elif self.is_valid_move(sel_row, sel_col, row, col):
                                self.make_move(sel_row, sel_col, row, col)
                                self.selected_square = None
                            else:
                                # If clicking own piece, select it
                                piece = self.board[row][col]
                                if piece and ((self.is_white and piece.isupper()) or
                                            (not self.is_white and piece.islower())):
                                    self.selected_square = (row, col)
                                else:
                                    # Invalid target, deselect
                                    self.selected_square = None
                        else:
                            # Check if square contains a piece that can be moved
                            piece = self.board[row][col]
                            if piece and ((self.is_white and piece.isupper()) or
                                        (not self.is_white and piece.islower())):
                                self.selected_square = (row, col)
                                
                        self.render()
            elif self.in_lobby:
                # Check for clicking on "Create Game" button
                create_button_x = 300
                create_button_y = 100
                create_button_width = 200
                create_button_height = 40
                
                if (create_button_x <= x <= create_button_x + create_button_width and
                    create_button_y <= y <= create_button_y + create_button_height):
                    self.send_to_server({
                        'type': 'create_game',
                        'name': self.player_name
                    })
                    return
                    
                # Check for clicking on a game in the list
                game_list_y = 200
                game_item_height = 40
                game_item_width = 300
                game_list_x = 250
                
                if (game_list_x <= x <= game_list_x + game_item_width):
                    game_index = (y - game_list_y) // game_item_height
                    if 0 <= game_index < len(self.available_games):
                        game = self.available_games[game_index]
                        self.send_to_server({
                            'type': 'join_game',
                            'game_id': game['id'],
                            'name': self.player_name
                        })
                        return
                        
                # Check for refresh button
                refresh_button_x = 500
                refresh_button_y = 150
                refresh_button_width = 100
                refresh_button_height = 30
                
                if (refresh_button_x <= x <= refresh_button_x + refresh_button_width and
                    refresh_button_y <= y <= refresh_button_y + refresh_button_height):
                    self.send_to_server({
                        'type': 'get_games'
                    })
                    return
    
    def handle_mousemove(self, event_parts):
        """Handle mouse move event"""
        if len(event_parts) >= 3:
            x = int(event_parts[1])
            y = int(event_parts[2])
            
            # Update hover state for board squares
            old_hover = self.hover_square
            self.hover_square = self.get_board_position(x, y)
            
            # Only re-render if hover state changed to reduce network traffic
            if old_hover != self.hover_square:
                self.render()
    
    def handle_resize(self, event_parts):
        """Handle resize event"""
        if len(event_parts) >= 3:
            self.canvas_width = int(event_parts[1])
            self.canvas_height = int(event_parts[2])
            
            # Adjust board position to center
            self.board_offset_x = (self.canvas_width - 8 * self.square_size) // 2
            self.board_offset_y = 70
            
            self.render()
    
    def render(self):
        """Render the game"""
        self.clear_screen()
        
        if self.in_lobby:
            self.render_lobby()
        elif self.in_game:
            self.render_game()
        
    def render_lobby(self):
        """Render the game lobby"""
        # Draw background
        self.draw_rect(0, 0, self.canvas_width, self.canvas_height, self.colors['background'])
        
        # Draw header
        self.draw_rect(0, 0, self.canvas_width, 50, self.colors['lobby_header'])
        self.draw_text(self.canvas_width // 2 - 100, 20, self.colors['light_text'], "Modern Chess - Game Lobby")
        
        # Draw create game button
        button_x = 300
        button_y = 100
        button_width = 200
        button_height = 40
        
        self.draw_rect(button_x, button_y, button_width, button_height, self.colors['button'])
        self.draw_text(button_x + 45, button_y + 10, self.colors['button_text'], "Create New Game")
        
        # Draw games section
        self.draw_text(250, 170, self.colors['text'], "Available Games:")
        
        # Draw refresh button
        refresh_x = 500
        refresh_y = 150
        refresh_width = 100
        refresh_height = 30
        
        self.draw_rect(refresh_x, refresh_y, refresh_width, refresh_height, self.colors['button'])
        self.draw_text(refresh_x + 25, refresh_y + 5, self.colors['button_text'], "Refresh")
        
        # Draw game list
        game_list_y = 200
        game_item_height = 40
        game_item_width = 300
        game_list_x = 250
        
        if len(self.available_games) == 0:
            self.draw_rect(game_list_x, game_list_y, game_item_width, game_item_height, self.colors['sidebar']) 
                  
        # Draw game list
        game_list_y = 200
        game_item_height = 40
        game_item_width = 300
        game_list_x = 250
        
        if len(self.available_games) == 0:
            self.draw_rect(game_list_x, game_list_y, game_item_width, game_item_height, self.colors['sidebar'])
            self.draw_text(game_list_x + 80, game_list_y + 15, self.colors['text'], "No games available")
        else:
            for i, game in enumerate(self.available_games):
                y = game_list_y + i * game_item_height
                
                # Draw game item with border
                self.draw_rect(game_list_x, y, game_item_width, game_item_height, self.colors['game_item'])
                self.draw_rect(game_list_x, y, game_item_width, 1, self.colors['divider'])  # Top border
                self.draw_rect(game_list_x, y + game_item_height - 1, game_item_width, 1, self.colors['divider'])  # Bottom border
                
                # Draw game info
                self.draw_text(game_list_x + 10, y + 10, self.colors['text'], 
                              f"Game #{game['id']} - Host: {game['host']}")
                
                # Draw join button
                join_x = game_list_x + game_item_width - 60
                join_y = y + 10
                self.draw_text(join_x, join_y, self.colors['button'], "Click to join")
        
        # Draw status bar at bottom
        status_height = 30
        self.draw_rect(0, self.canvas_height - status_height, self.canvas_width, status_height, self.colors['header_bg'])
        self.draw_text(20, self.canvas_height - status_height + 8, self.colors['light_text'], f"Player: {self.player_name}")
        self.draw_text(self.canvas_width - 300, self.canvas_height - status_height + 8, self.colors['light_text'], f"Status: {self.message}")
        
    def render_game(self):
        """Render the chess game"""
        # Draw background
        self.draw_rect(0, 0, self.canvas_width, self.canvas_height, self.colors['background'])
        
        # Draw header
        self.draw_rect(0, 0, self.canvas_width, 50, self.colors['header_bg'])
        header_text = "Modern Chess"
        self.draw_text(20, 20, self.colors['light_text'], header_text)
        
        # Draw players info in header
        player_info_x = self.canvas_width - 300
        self.draw_text(player_info_x, 15, self.colors['light_text'], f"You: {self.player_name}")
        self.draw_text(player_info_x, 35, self.colors['light_text'], f"Opponent: {self.opponent_name}")
        
        # Draw turn indicator in header
        turn_text = "Your Turn" if self.players_turn else "Opponent's Turn"
        turn_color = self.colors['status_good'] if self.players_turn else self.colors['light_text']
        turn_x = self.canvas_width // 2 - 40
        self.draw_text(turn_x, 20, turn_color, turn_text)
        
        # Draw board border
        border = 2
        self.draw_rect(
            self.board_offset_x - border, self.board_offset_y - border,
            self.square_size * 8 + border * 2, self.square_size * 8 + border * 2,
            self.colors['board_border']
        )
        
        # Draw board squares
        for row in range(8):
            for col in range(8):
                # Get screen position
                x, y = self.get_screen_position(row, col)
                
                # Determine square color
                if (row + col) % 2 == 0:
                    color = self.colors['light_square']
                else:
                    color = self.colors['dark_square']
                    
                # Highlight selected square
                if self.selected_square and self.selected_square == (row, col):
                    color = self.colors['selected']
                    
                # Highlight hovered square
                elif self.hover_square and self.hover_square == (row, col):
                    # Only highlight if it's a valid target or own piece
                    piece = self.board[row][col]
                    if ((self.selected_square and 
                         self.is_valid_move(self.selected_square[0], self.selected_square[1], row, col)) or
                        (piece and ((self.is_white and piece.isupper()) or 
                                   (not self.is_white and piece.islower())))):
                        color = self.colors['hover']
                    
                # Highlight last move
                if self.last_move and (row, col) in [(self.last_move[0], self.last_move[1]), 
                                                    (self.last_move[2], self.last_move[3])]:
                    color = self.colors['last_move']
                
                # Draw square
                self.draw_rect(x, y, self.square_size, self.square_size, color)
                
                # If there's a piece on this square, draw it
                piece = self.board[row][col]
                if piece:
                    piece_char = self.piece_chars.get(piece, '?')
                    piece_color = self.colors['white_piece'] if piece.isupper() else self.colors['black_piece']
                    # Draw centered in square
                    self.draw_text(x + self.square_size // 2 - 10, 
                                  y + self.square_size // 2 - 14,
                                  piece_color, piece_char)
        
        # Draw row numbers and column letters
        for i in range(8):
            row_label = str(8 - i) if self.is_white else str(i + 1)
            col_label = chr(97 + i) if self.is_white else chr(104 - i)
            
            # Row numbers - more minimal and aligned with board
            row_y = self.board_offset_y + i * self.square_size + self.square_size // 2 - 7
            self.draw_text(self.board_offset_x - 20, row_y, self.colors['text'], row_label)
            
            # Column letters - more minimal and aligned with board
            col_x = self.board_offset_x + i * self.square_size + self.square_size // 2 - 5
            self.draw_text(col_x, self.board_offset_y + 8 * self.square_size + 20, 
                          self.colors['text'], col_label)
        
        # Draw valid moves for selected piece
        if self.selected_square and self.players_turn:
            row, col = self.selected_square
            valid_moves = self.get_valid_moves(row, col)
            
            for move_row, move_col in valid_moves:
                x, y = self.get_screen_position(move_row, move_col)
                # Draw a small circle to indicate valid move
                circle_size = self.square_size // 5
                circle_x = x + (self.square_size - circle_size) // 2
                circle_y = y + (self.square_size - circle_size) // 2
                
                # If target square has a piece (capture), draw a different indicator
                if self.board[move_row][move_col] is not None:
                    # Draw a ring instead of a circle for captures
                    ring_size = self.square_size // 2
                    ring_thickness = 3
                    ring_x = x + (self.square_size - ring_size) // 2
                    ring_y = y + (self.square_size - ring_size) // 2
                    
                    # Outer circle
                    self.draw_rect(ring_x, ring_y, ring_size, ring_thickness, self.colors['valid_move'])
                    self.draw_rect(ring_x, ring_y, ring_thickness, ring_size, self.colors['valid_move'])
                    self.draw_rect(ring_x + ring_size - ring_thickness, ring_y, ring_thickness, ring_size, self.colors['valid_move'])
                    self.draw_rect(ring_x, ring_y + ring_size - ring_thickness, ring_size, ring_thickness, self.colors['valid_move'])
                else:
                    # Simple dot for empty square moves
                    self.draw_rect(circle_x, circle_y, circle_size, circle_size, self.colors['valid_move'])
        
        # Draw game info sidebar
        sidebar_x = self.board_offset_x + 8 * self.square_size + 20
        sidebar_y = self.board_offset_y
        sidebar_width = 200
        sidebar_height = 8 * self.square_size
        
        # Draw sidebar background
        self.draw_rect(sidebar_x, sidebar_y, sidebar_width, sidebar_height, self.colors['sidebar'])
        
        # Draw sidebar content
        text_x = sidebar_x + 15
        text_y = sidebar_y + 20
        
        # Playing as
        self.draw_text(text_x, text_y, self.colors['text'], f"Playing as: {'White' if self.is_white else 'Black'}")
        
        # Game info
        if self.game_id:
            self.draw_text(text_x, text_y + 30, self.colors['text'], f"Game #{self.game_id}")
            
        # Draw turn status with colored indicator
        status_y = text_y + 70
        if self.players_turn:
            status_color = self.colors['status_good']
            status_text = "Your Turn"
        else:
            status_color = self.colors['status_warning']
            status_text = "Opponent's Turn"
        
        # Draw colored dot
        dot_size = 10
        self.draw_rect(text_x, status_y, dot_size, dot_size, status_color)
        self.draw_text(text_x + 20, status_y, self.colors['text'], status_text)
        
        # Draw last move
        if self.last_move:
            from_row, from_col, to_row, to_col = self.last_move
            from_str = f"{chr(97 + from_col)}{8 - from_row}"
            to_str = f"{chr(97 + to_col)}{8 - to_row}"
            move_text = f"Last move: {from_str} → {to_str}"
            self.draw_text(text_x, status_y + 30, self.colors['text'], move_text)
        
        # Draw status bar
        self.draw_rect(0, self.canvas_height - 30, self.canvas_width, 30, self.colors['header_bg'])
        self.draw_text(20, self.canvas_height - 22, self.colors['light_text'], f"Status: {self.message}")
        
        # Draw game over message if game is over
        if self.is_game_over:
            # Draw semi-transparent overlay
            overlay_color = "#00000088"
            self.draw_rect(0, 0, self.canvas_width, self.canvas_height, overlay_color)
            
            # Draw game over panel
            panel_width = 400
            panel_height = 150
            panel_x = (self.canvas_width - panel_width) // 2
            panel_y = (self.canvas_height - panel_height) // 2
            
            # Draw panel background
            self.draw_rect(panel_x, panel_y, panel_width, panel_height, "#FFFFFF")
            
            # Draw game over title
            self.draw_text(panel_x + 150, panel_y + 40, "#000000", "Game Over")
            
            # Draw result message
            self.draw_text(panel_x + 50, panel_y + 80, "#000000", self.message)
            
            # Draw return to lobby hint
            self.draw_text(panel_x + 70, panel_y + 120, "#666666", "Refresh the page to return to lobby")


def main():
    parser = argparse.ArgumentParser(description='Modern Chess Game Client')
    parser.add_argument('--host', default='localhost', help='Canvas server host')
    parser.add_argument('--port', type=int, default=5005, help='Canvas server port')
    parser.add_argument('--server-host', default='localhost', help='Game server host')
    parser.add_argument('--server-port', type=int, default=5006, help='Game server port')
    parser.add_argument('--name', help='Player name')
    
    args = parser.parse_args()
    
    client = ModernChessClient(args.host, args.port, args.server_host, args.server_port, args.name)
    
    if client.connect():
        # Register event handlers
        client.on('resize', client.handle_resize)
        client.on('mousedown', client.handle_mousedown)
        client.on('mousemove', client.handle_mousemove)
        
        # Initial render
        client.render()
        
        try:
            while True:
                time.sleep(0.1)
                
                if not client.connected or not client.server_connected:
                    print("Connection lost. Exiting...")
                    break
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            client.disconnect()
    else:
        print("Failed to connect. Make sure servers are running.")


if __name__ == "__main__":
    main()