from fastapi import FastAPI
from pydantic import BaseModel
import chess
import chess.engine
import random

app = FastAPI()

# Initialize chess board
board = chess.Board()

class MoveRequest(BaseModel):
    source: str
    target: str

class MoveResponse(BaseModel):
    valid: bool
    board: str
    status: str

@app.post("/make-move", response_model=MoveResponse)
async def make_move(move: MoveRequest):
    # Attempt to make the player's move
    try:
        move_obj = chess.Move.from_uci(f"{move.source}{move.target}")
        if move_obj in board.legal_moves:
            board.push(move_obj)
            status = "AI's turn"
            
            # AI's move (this is a simple random AI, replace with a more sophisticated AI if needed)
            ai_move = random.choice(list(board.legal_moves))
            board.push(ai_move)
            status = "Player's turn"
            
            return MoveResponse(
                valid=True,
                board=board.fen(),  # Send the updated board in FEN format
                status=status
            )
        else:
            return MoveResponse(
                valid=False,
                board=board.fen(),
                status="Player's turn"
            )
    except Exception as e:
        print(f"Error processing move: {e}")
        return MoveResponse(
            valid=False,
            board=board.fen(),
            status="Player's turn"
        )
