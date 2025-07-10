from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .tictactoe import (
    Move, GameState, StartGameResponse, MakeMoveResponse,
    GameHistoryResponse, GameHistoryItem, game_store, apply_move, create_game_state_response
)

description = """
Backend API for Tic Tac Toe.  
- Start new game  
- Make move  
- Get game state  
- Retrieve history of games  
"""

openapi_tags = [
    {"name": "Games", "description": "Endpoints to play and manage games"},
    {"name": "History", "description": "Retrieve completed and in-progress games"}
]

app = FastAPI(
    title="Tic Tac Toe API",
    description=description,
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", summary="Health Check")
def health_check():
    """
    Returns a simple health status.
    """
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post("/game/start", response_model=StartGameResponse, tags=["Games"], summary="Start a new Tic Tac Toe game", status_code=201)
def start_game():
    """
    Start a new Tic Tac Toe game.

    Returns a unique game ID and the initial state of the game.
    """
    game_id = game_store.create_game()
    state = create_game_state_response(game_id, game_store.get_game(game_id))
    return StartGameResponse(game_id=game_id, state=state)

# PUBLIC_INTERFACE
@app.post("/game/{game_id}/move", response_model=MakeMoveResponse, tags=["Games"], summary="Make a move in a game")
def make_move(game_id: str, move: Move):
    """
    Make a move in the given Tic Tac Toe game.

    Parameters:
    - **game_id**: ID of the game
    - **move**: Move object with row, column, and player (X or O)

    Returns the updated game state.
    """
    try:
        state = apply_move(game_id, move)
        return MakeMoveResponse(state=state)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

# PUBLIC_INTERFACE
@app.get("/game/{game_id}/state", response_model=GameState, tags=["Games"], summary="Get current state of a game")
def get_game_state(game_id: str):
    """
    Get the current state of the specified game.

    Parameters:
    - **game_id**: ID of the game

    Returns game board, current player, and other state info.
    """
    game = game_store.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return create_game_state_response(game_id, game)

# PUBLIC_INTERFACE
@app.get("/game/history", response_model=GameHistoryResponse, tags=["History"], summary="Get history of all games")
def get_game_history():
    """
    Get the list and summary of all games played so far.

    Returns game IDs, status, winner, and move count for each.
    """
    games = game_store.all_games()
    history = []
    for gid, game in games.items():
        history.append(
            GameHistoryItem(
                game_id=gid,
                status=game["status"],
                winner=game["winner"],
                moves_count=len(game["moves"]),
            )
        )
    return GameHistoryResponse(history=history)
