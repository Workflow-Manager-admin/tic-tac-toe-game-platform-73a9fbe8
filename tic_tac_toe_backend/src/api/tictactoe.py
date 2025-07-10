from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

# --- Enums and Data Models ---

class Player(str, Enum):
    X = "X"
    O = "O"

class CellState(str, Enum):
    EMPTY = " "
    X = "X"
    O = "O"

class GameStatus(str, Enum):
    ONGOING = "ongoing"
    DRAW = "draw"
    X_WON = "x_won"
    O_WON = "o_won"

# PUBLIC_INTERFACE
class Move(BaseModel):
    """Model for a move made by a player."""
    player: Player = Field(..., description="Player making the move ('X' or 'O').")
    row: int = Field(..., description="Row index (0-2)")
    col: int = Field(..., description="Column index (0-2)")

# PUBLIC_INTERFACE
class GameState(BaseModel):
    """Model for returning the state of the game."""
    game_id: str = Field(..., description="Unique ID of the game")
    board: List[List[CellState]] = Field(..., description="Current state of the 3x3 board")
    current_player: Player = Field(..., description="Player who should move next")
    status: GameStatus = Field(..., description="Current status of the game")
    winner: Optional[Player] = Field(None, description="Winner of the game, if any")
    moves: List[Move] = Field(..., description="List of moves in order")

# PUBLIC_INTERFACE
class StartGameResponse(BaseModel):
    """Response returned after starting a new game."""
    game_id: str = Field(..., description="Unique ID of the new game")
    state: GameState = Field(..., description="Current state of the new game")

# PUBLIC_INTERFACE
class MakeMoveResponse(BaseModel):
    """Response returned after a move is made."""
    state: GameState = Field(..., description="Updated state of the game")

# PUBLIC_INTERFACE
class GameHistoryItem(BaseModel):
    """Item in the game history list."""
    game_id: str
    status: GameStatus
    winner: Optional[Player]
    moves_count: int

# PUBLIC_INTERFACE
class GameHistoryResponse(BaseModel):
    """List of all past games and their basic info."""
    history: List[GameHistoryItem]

# --- In-Memory Storage Layer (for demo or light usage) ---

class InMemoryGameStore:
    """A lightweight, thread-unsafe in-memory store for demo/single-process use."""
    def __init__(self):
        self.games: Dict[str, Dict[str, Any]] = {}

    # PUBLIC_INTERFACE
    def create_game(self) -> str:
        """Create a new game and return its unique ID."""
        game_id = str(uuid4())
        self.games[game_id] = {
            "board": [[CellState.EMPTY for _ in range(3)] for _ in range(3)],
            "current_player": Player.X,
            "status": GameStatus.ONGOING,
            "winner": None,
            "moves": []
        }
        return game_id

    # PUBLIC_INTERFACE
    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get internal dict representing the game state."""
        return self.games.get(game_id)

    # PUBLIC_INTERFACE
    def list_games(self) -> List[str]:
        """List all game IDs (active and completed)."""
        return list(self.games.keys())

    # PUBLIC_INTERFACE
    def update_game(self, game_id: str, data: Dict[str, Any]):
        """Overwrite the game state."""
        self.games[game_id] = data

    # PUBLIC_INTERFACE
    def all_games(self) -> Dict[str, Dict[str, Any]]:
        """Return the dict of all games."""
        return self.games

# Singleton store
game_store = InMemoryGameStore()

# --- Game Logic Functions ---

# PUBLIC_INTERFACE
def check_winner(board: List[List[CellState]]) -> Optional[Player]:
    """Returns the winner (Player.X/Player.O) or None if no winner yet."""
    for p in (Player.X, Player.O):
        # Check rows, columns
        for i in range(3):
            if all(board[i][j] == p for j in range(3)):
                return p
            if all(board[j][i] == p for j in range(3)):
                return p
        # Check diagonals
        if all(board[i][i] == p for i in range(3)):
            return p
        if all(board[i][2 - i] == p for i in range(3)):
            return p
    return None

# PUBLIC_INTERFACE
def is_board_full(board: List[List[CellState]]) -> bool:
    """Returns True if the board is full (no EMPTY)."""
    return all(cell != CellState.EMPTY for row in board for cell in row)

# PUBLIC_INTERFACE
def create_game_state_response(game_id: str, game_dict: Dict[str, Any]) -> GameState:
    """Build a GameState model from the internal game dict."""
    return GameState(
        game_id=game_id,
        board=game_dict["board"],
        current_player=game_dict["current_player"],
        status=game_dict["status"],
        winner=game_dict["winner"],
        moves=game_dict["moves"]
    )

# PUBLIC_INTERFACE
def apply_move(game_id: str, move: Move) -> GameState:
    """Applies a move to the game if valid and returns the updated state."""
    game = game_store.get_game(game_id)
    if not game:
        raise ValueError("Game not found")

    row, col = move.row, move.col
    # Enforce rules
    if not (0 <= row < 3 and 0 <= col < 3):
        raise ValueError("Move out of bounds")
    if game["board"][row][col] != CellState.EMPTY:
        raise ValueError("Cell already occupied")
    if game["status"] != GameStatus.ONGOING:
        raise ValueError("Game already completed")
    if move.player != game["current_player"]:
        raise ValueError("Not this player's turn")

    # Make the move
    game["board"][row][col] = move.player
    game["moves"].append(move)

    winner = check_winner(game["board"])
    if winner:
        game["status"] = GameStatus.X_WON if winner == Player.X else GameStatus.O_WON
        game["winner"] = winner
    elif is_board_full(game["board"]):
        game["status"] = GameStatus.DRAW
        game["winner"] = None
    else:
        game["current_player"] = Player.O if move.player == Player.X else Player.X

    game_store.update_game(game_id, game)
    return create_game_state_response(game_id, game)
