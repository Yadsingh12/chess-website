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
    winner: str = None  # 'white', 'black', or 'draw'
    reset: bool = False  # Signal to reset the game
    request_promotion: bool = False  # To indicate a promotion is needed
    promotion_piece: str = None  # To ask for the piece during promotion (if applicable)


@app.post("/make-move", response_model=MoveResponse)
async def make_move(move: MoveRequest):
    global board  # Ensure we are modifying the global board object

    try:
        print("hi")
        if move.promotion:
            print("yo yo promotion")
            move_obj = chess.Move.from_uci(
                f"{move.source}{move.target}{move.promotion}"
            )
        else:
            move_obj = chess.Move.from_uci(f"{move.source}{move.target}")
            # If the piece being moved is a pawn and reaches the last rank, handle promotion
            piece = board.piece_at(move_obj.from_square)
            print(piece.symbol(), type(piece.symbol()))
            if piece.symbol() == "P":
                print("it is pawn")
                if (
                    move_obj.from_square // 8 == 6 and move_obj.to_square // 8 == 7
                ):  # Player's pawn reaching 8th rank
                    # Pawn reaches last rank, ask for promotion
                    print("wtf")
                    move_obj = chess.Move.from_uci(f"{move.source}{move.target}q")
                    if move_obj in board.legal_moves:
                        print("requesting promotion")
                        return MoveResponse(
                            valid=True,
                            board=board.fen(),
                            status="Pawn promotion! Choose a piece (q/r/b/n).",
                            request_promotion=True,
                        )

        # Check if the move is legal
        if move_obj in board.legal_moves:
            # Apply the move to the board
            board.push(move_obj)

            # Check if the game is over after the player's move
            if board.is_checkmate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Checkmate! Player wins.",
                    winner="player",
                    reset=True,  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_stalemate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Stalemate! It's a draw.",
                    winner="draw",
                    reset=True,  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_check():
                status = "AI's turn (Check)"
            else:
                status = "AI's turn"

            # AI makes a move (for simplicity, random move)
            ai_move = random.choice(list(board.legal_moves))

            board.push(ai_move)

            # Check if the game is over after the AI's move
            if board.is_checkmate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Checkmate! AI wins.",
                    winner="ai",
                    reset=True,  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_stalemate():
                response = MoveResponse(
                    valid=True,
                    board=board.fen(),
                    status="Stalemate! It's a draw.",
                    winner="draw",
                    reset=True,  # Indicate that the game should reset
                )
                board = chess.Board()  # Reset the board for the next game
                return response
            elif board.is_check():
                status = "Player's turn (Check)"
            else:
                status = "Player's turn"

            return MoveResponse(valid=True, board=board.fen(), status=status)
        else:
            return MoveResponse(valid=False, board=board.fen(), status="Player's turn")
    except Exception as e:
        print(f"Error: {e}")
        return MoveResponse(valid=False, board=board.fen(), status="Player's turn")
