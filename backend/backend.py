from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import random

app = FastAPI()

# CORS configuration: Allow requests from localhost:5500 (your frontend)
origins = [
    "http://127.0.0.1:5500",  # Allow your frontend to access the backend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # The list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Chess game logic
board = chess.Board()

class MoveRequest(BaseModel):
    source: str
    target: str
    promotion: str = None  # Optional promotion piece (e.g., 'q' for queen)

class MoveResponse(BaseModel):
    valid: bool
    board: str
    status: str
    game_over: bool = False
    winner: str = None  # 'white', 'black', or 'draw'
    reset: bool = False  # Signal to reset the game

@app.post("/make-move", response_model=MoveResponse)
async def make_move(move: MoveRequest):
    global board  # Ensure we are modifying the global board object
    
    try:
        move_obj = chess.Move.from_uci(f"{move.source}{move.target}")

        # Check if the move is legal
        if move_obj in board.legal_moves:
            # If the piece being moved is a pawn and reaches the last rank, handle promotion
            piece = board.piece_at(move_obj.from_square)
            if piece == chess.PAWN:
                if move_obj.from_square // 8 == 6 and move_obj.to_square // 8 == 7:  # Player's pawn reaching 8th rank
                    if move.promotion:
                        # Apply the promotion based on the piece selected by the player
                        move_obj = chess.Move(move_obj.from_square, move_obj.to_square, promotion=move.promotion)
                    else:
                        # Ask for promotion (this will be handled in the frontend)
                        return MoveResponse(
                            valid=True,
                            board=board.fen(),
                            status="Pawn promotion! Choose a piece (q/r/b/n).",
                            request_promotion=True,
                            promotion_piece=None
                        )
                elif move_obj.from_square // 8 == 1 and move_obj.to_square // 8 == 0:  # AI's pawn reaching 1st rank
                    # Pawn reaches last rank, promote to Queen (AI's automatic promotion)
                    move_obj = chess.Move(move_obj.from_square, move_obj.to_square, promotion='q')  # Promote to Queen

            # Apply the move to the board
            board.push(move_obj)
            
            # Check if the game is over after the player's move
            if board.is_checkmate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Checkmate! Player wins.",
                    game_over=True,
                    winner="player",
                    reset=True  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_stalemate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Stalemate! It's a draw.",
                    game_over=True,
                    winner="draw",
                    reset=True  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_check():
                status = "AI's turn (Check)"
            else:
                status = "AI's turn"
            
            # AI makes a move (for simplicity, random move)
            ai_move = random.choice(list(board.legal_moves))
            
            # If the AI's pawn reaches the last row, promote it
            ai_piece = board.piece_at(ai_move.from_square)
            if ai_piece == chess.PAWN:
                if ai_move.from_square // 8 == 1 and ai_move.to_square // 8 == 0:  # AI's pawn moves to 1st rank
                    ai_move = chess.Move(ai_move.from_square, ai_move.to_square, promotion='q')  # Promote to Queen

            board.push(ai_move)

            # Check if the game is over after the AI's move
            if board.is_checkmate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Checkmate! AI wins.",
                    game_over=True,
                    winner="ai",
                    reset=True  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_stalemate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Stalemate! It's a draw.",
                    game_over=True,
                    winner="draw",
                    reset=True  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_check():
                status = "Player's turn (Check)"
            else:
                status = "Player's turn"

            return MoveResponse(
                valid=True,
                board=board.fen(),
                status=status
            )
        else:
            return MoveResponse(
                valid=False,
                board=board.fen(),
                status="Player's turn"
            )
    except Exception as e:
        print(f"Error: {e}")
        return MoveResponse(
            valid=False,
            board=board.fen(),
            status="Player's turn"
        )
