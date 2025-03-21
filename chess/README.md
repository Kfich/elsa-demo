# Chess Game Platform

A multiplayer chess game built using the socket canvas infrastructure.

## Features

- Full chess game with proper piece movement rules
- Game lobby for creating and joining games
- Real-time multiplayer gameplay
- Visual highlighting of valid moves
- Last move indicator
- Game state tracking
- Win/loss detection

## Project Structure

```
chess/
│
├── socket_canvas.py           # Provided canvas API for drawing
│
├── chess_client.py            # Chess game client
│
├── chess_server.py            # Game server for multiplayer
│
└── chess.py               # Helper script to run all components
```

## Architecture

This project uses a client-server architecture with two server components:

1. **Canvas Server**: Provides the drawing surface and input handling via `socket_canvas.py`
2. **Game Server**: Manages game logic, state, and player connections via `chess_server.py`

The clients connect to both servers:
- Canvas connection for display and input
- Game server connection for game logic and player communication

## Setup and Running

### Prerequisites
- Python 3.x
- Tkinter (included with most Python installations)

### Running with the Helper Script

The easiest way to start all components is with the provided helper script:

```bash
# Start with a single client
python run_chess.py --name YourName

# Start with two clients (for testing on one computer)
python run_chess.py --players 2
```

### Starting Components Manually

You can also start each component individually:

1. First, start the socket canvas:
```bash
python socket_canvas.py
```

2. Then, start the chess server:
```bash
python chess_server.py
```

3. Finally, start one or more client instances:
```bash
python chess_client.py --name Player1
```

## How to Play

### Game Lobby
1. When you first start the client, you'll see the game lobby
2. Click "Create New Game" to create a new game and wait for an opponent
3. Or join an existing game by clicking on it in the list
4. Click "Refresh" to update the list of available games

### Playing Chess
1. The game board is displayed with your pieces (white or black)
2. White always moves first
3. Click on a piece to select it
4. Valid moves will be highlighted on the board
5. Click on a valid destination square to move the piece
6. The last move is highlighted on the board
7. The game continues until one player wins or a draw is declared

### Game Rules
- Standard chess rules are implemented
- Pawns can move one square forward or two on their first move
- Pawns capture diagonally
- Pawns are automatically promoted to Queens when they reach the opposite end
- Knights move in an L-shape pattern
- Bishops move diagonally
- Rooks move horizontally or vertically
- Queens can move like rooks or bishops
- Kings move one square in any direction
- A player wins by capturing the opponent's king

## Technical Implementation

The chess game implementation includes:

### Client Components
- **Board Rendering**: Draws the chess board, pieces, and UI elements
- **Piece Movement**: Handles piece selection and movement validation
- **Game State Management**: Tracks the current state of the game
- **Networking**: Communicates with both the canvas and game servers

### Server Components
- **Game Logic**: Validates moves and manages game state
- **Player Management**: Handles player connections, matchmaking, and turn order
- **Game Lobby**: Allows players to create and join games

## Future Enhancements

- Add castling and en passant special moves
- Implement check and checkmate detection
- Add time controls
- Support for saving and loading games
- Add spectator mode
- Sound effects
- User accounts and rankings
- Game history and replay

## Troubleshooting

If you encounter issues:
1. Ensure all components are running in the correct order (canvas, server, then clients)
2. Check that the ports are not in use by other applications
3. Verify you have proper permissions to open network connections
4. Try restarting all components if connections fail

### Common Issues

- **Cannot connect to canvas**: Ensure socket_canvas.py is running
- **Cannot connect to server**: Check that chess_server.py is running and the port is correct
- **Game not appearing in lobby**: Try clicking the refresh button
- **Cannot move pieces**: Ensure it's your turn and you're selecting valid moves

## Acknowledgments

This chess implementation uses the socket canvas infrastructure for rendering, which provides a simple way to create interactive applications with minimal dependencies. The game logic and networking are built on top of this infrastructure to create a complete multiplayer experience.