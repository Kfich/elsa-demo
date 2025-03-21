#!/usr/bin/env python3
import socket
import threading
import json
import time
import argparse
import random

class ChessGame:
    """Represents a chess game between two players"""
    def __init__(self, game_id, host_player):
        self.id = game_id
        self.host = host_player
        self.guest = None
        self.board = self.create_initial_board()
        self.current_turn = 'white'  # White always goes first
        self.moves = []
        self.is_over = False
        self.winner = None
        self.result = None
        
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
        
    def make_move(self, from_row, from_col, to_row, to_col):
        """Make a move and update the board"""
        # Record the move
        self.moves.append({
            'from_row': from_row,
            'from_col': from_col,
            'to_row': to_row,
            'to_col': to_col,
            'piece': self.board[from_row][from_col],
            'captured': self.board[to_row][to_col],
            'turn': self.current_turn
        })
        
        # Move the piece
        piece = self.board[from_row][from_col]
        self.board[from_row][from_col] = None
        self.board[to_row][to_col] = piece
        
        # Check for pawn promotion
        if piece.upper() == 'P' and (to_row == 0 or to_row == 7):
            # Promote to queen
            self.board[to_row][to_col] = 'Q' if piece.isupper() else 'q'
            
        # Check for game-ending conditions
        self.check_game_over()
        
        # Switch turns
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        
    def check_game_over(self):
        """Check if the game is over"""
        # Check if kings are still on the board
        white_king_exists = False
        black_king_exists = False
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == 'K':
                    white_king_exists = True
                elif piece == 'k':
                    black_king_exists = True
        
        if not white_king_exists:
            self.is_over = True
            self.winner = self.guest if self.host.is_white else self.host
            self.result = "checkmate"
        elif not black_king_exists:
            self.is_over = True
            self.winner = self.host if self.host.is_white else self.guest
            self.result = "checkmate"
            
        # For simplicity, we're not implementing more complex checks like stalemate,
        # insufficient material, etc.
        
        # If the game has been going on for too long, it's a draw
        if len(self.moves) > 200:
            self.is_over = True
            self.winner = None
            self.result = "50-move rule"

class Player:
    """Represents a player in the chess server"""
    def __init__(self, client_id, socket, address, name=None):
        self.id = client_id
        self.socket = socket
        self.address = address
        self.name = name or f"Player-{client_id[-4:]}"
        self.is_white = None  # Will be set when joining a game
        self.current_game = None
        
    def send_message(self, data):
        """Send a message to the player"""
        try:
            message = json.dumps(data) + '\n'
            self.socket.sendall(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending to player {self.name}: {e}")
            return False

class ChessServer:
    """Chess game server that manages games and communication"""
    def __init__(self, host='localhost', port=5006):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.players = {}  # {client_id: Player}
        self.games = {}    # {game_id: ChessGame}
        self.next_game_id = 1
        
    def start(self):
        """Start the chess server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"Chess server started on {self.host}:{self.port}")
            
            # Accept client connections
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_id = str(id(client_socket))
                    
                    # Create new player
                    player = Player(client_id, client_socket, client_address)
                    self.players[client_id] = player
                    
                    print(f"New player connected: {client_address} (ID: {client_id})")
                    
                    # Create thread to handle this player
                    client_thread = threading.Thread(target=self.handle_player, args=(client_id,))
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    if not self.running:
                        break
            
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the chess server"""
        self.running = False
        
        # Close all client connections
        for player_id in list(self.players.keys()):
            self.disconnect_player(player_id)
            
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        print("Chess server stopped")
        
    def handle_player(self, player_id):
        """Handle messages from a player"""
        if player_id not in self.players:
            return
            
        player = self.players[player_id]
        buffer = ""
        
        while self.running and player_id in self.players:
            try:
                data = player.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                
                # Process complete messages (ones that end with newline)
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    self.process_player_message(player_id, message)
                    
            except Exception as e:
                print(f"Error receiving from player {player_id}: {e}")
                break
                
        # Player disconnected or error
        self.disconnect_player(player_id)
        
    def process_player_message(self, player_id, message):
        """Process a message received from a player"""
        if player_id not in self.players:
            return
            
        player = self.players[player_id]
        
        try:
            # Parse the message (should be JSON)
            data = json.loads(message)
            
            message_type = data.get('type')
            
            if message_type == 'join_lobby':
                # Player is joining the lobby
                name = data.get('name')
                if name:
                    player.name = name
                
                # Send list of available games
                self.send_game_list(player_id)
                
            elif message_type == 'get_games':
                # Player is requesting list of games
                self.send_game_list(player_id)
                
            elif message_type == 'create_game':
                # Player is creating a new game
                name = data.get('name')
                if name:
                    player.name = name
                    
                # Create a new game
                game_id = self.next_game_id
                self.next_game_id += 1
                
                # Randomly decide if host plays white or black
                player.is_white = random.choice([True, False])
                
                # Create game with this player as host
                game = ChessGame(game_id, player)
                self.games[game_id] = game
                
                # Update player's current game
                player.current_game = game
                
                # Notify player
                player.send_message({
                    'type': 'game_created',
                    'game_id': game_id,
                    'is_white': player.is_white
                })
                
                print(f"Game {game_id} created by {player.name}")
                
                # Update game list for all players in lobby
                self.broadcast_game_list()
                
            elif message_type == 'join_game':
                # Player is joining an existing game
                game_id = data.get('game_id')
                name = data.get('name')
                
                if name:
                    player.name = name
                
                if game_id in self.games:
                    game = self.games[game_id]
                    
                    # Check if the game already has two players
                    if game.guest is not None:
                        player.send_message({
                            'type': 'error',
                            'message': 'Game is already full'
                        })
                        return
                        
                    # Add player as guest
                    game.guest = player
                    player.current_game = game
                    
                    # Set player color (opposite of host)
                    player.is_white = not game.host.is_white
                    
                    # Notify both players
                    player.send_message({
                        'type': 'game_joined',
                        'game_id': game_id,
                        'is_white': player.is_white,
                        'opponent': game.host.name
                    })
                    
                    game.host.send_message({
                        'type': 'opponent_joined',
                        'opponent': player.name
                    })
                    
                    print(f"Player {player.name} joined game {game_id}")
                    
                    # Update game list for all players in lobby
                    self.broadcast_game_list()
                else:
                    player.send_message({
                        'type': 'error',
                        'message': 'Game not found'
                    })
                    
            elif message_type == 'move':
                # Player is making a move
                game_id = data.get('game_id')
                move = data.get('move')
                
                if game_id in self.games and move:
                    game = self.games[game_id]
                    
                    # Check if it's this player's turn
                    is_white_turn = game.current_turn == 'white'
                    is_player_turn = (player.is_white == is_white_turn)
                    
                    if not is_player_turn:
                        player.send_message({
                            'type': 'error',
                            'message': 'Not your turn'
                        })
                        return
                    
                    # Make the move
                    try:
                        from_row = move.get('from_row')
                        from_col = move.get('from_col')
                        to_row = move.get('to_row')
                        to_col = move.get('to_col')
                        
                        game.make_move(from_row, from_col, to_row, to_col)
                        
                        # Notify the other player
                        opponent = game.guest if player == game.host else game.host
                        opponent.send_message({
                            'type': 'move',
                            'move': move
                        })
                        
                        # If the game is over, notify both players
                        if game.is_over:
                            winner_name = game.winner.name if game.winner else None
                            
                            for p in [game.host, game.guest]:
                                p.send_message({
                                    'type': 'game_over',
                                    'winner': winner_name,
                                    'result': game.result
                                })
                                
                            print(f"Game {game_id} is over. Result: {game.result}")
                        
                    except Exception as e:
                        player.send_message({
                            'type': 'error',
                            'message': f'Invalid move: {str(e)}'
                        })
                else:
                    player.send_message({
                        'type': 'error',
                        'message': 'Game not found or invalid move data'
                    })
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON from player {player_id}: {message}")
        except Exception as e:
            print(f"Error processing message from player {player_id}: {e}")
            
    def send_game_list(self, player_id):
        """Send list of available games to a player"""
        if player_id not in self.players:
            return
            
        player = self.players[player_id]
        
        # Collect available games (games with only one player)
        available_games = []
        for game_id, game in self.games.items():
            if game.guest is None and not game.is_over:
                available_games.append({
                    'id': game_id,
                    'host': game.host.name
                })
        
        # Send to player
        player.send_message({
            'type': 'game_list',
            'games': available_games
        })
        
    def broadcast_game_list(self):
        """Send updated game list to all players in the lobby"""
        for player_id, player in self.players.items():
            if player.current_game is None:
                self.send_game_list(player_id)
                
    def disconnect_player(self, player_id):
        """Handle player disconnection"""
        if player_id not in self.players:
            return
            
        player = self.players[player_id]
        
        # Handle the game this player is in
        if player.current_game:
            game = player.current_game
            
            # If the player was in a game, notify the opponent
            if game.host == player and game.guest:
                # Host left, notify guest
                game.guest.send_message({
                    'type': 'game_over',
                    'winner': game.guest.name,
                    'result': 'opponent_disconnected'
                })
                game.guest.current_game = None
                
            elif game.guest == player:
                # Guest left, notify host
                game.host.send_message({
                    'type': 'game_over',
                    'winner': game.host.name,
                    'result': 'opponent_disconnected'
                })
                game.host.current_game = None
                
            # Remove the game
            if game.id in self.games:
                del self.games[game.id]
                
            # Update game list for all players in lobby
            self.broadcast_game_list()
            
        # Close socket
        try:
            player.socket.close()
        except:
            pass
            
        # Remove from players dictionary
        del self.players[player_id]
        
        print(f"Player disconnected: {player_id} ({player.name})")

def main():
    parser = argparse.ArgumentParser(description='Chess Game Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=5006, help='Server port')
    
    args = parser.parse_args()
    
    server = ChessServer(args.host, args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()