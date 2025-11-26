import os
import logging
import asyncio
import ssl
import random
from slixmpp import ClientXMPP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

class XMPPAgent(ClientXMPP):
    def __init__(self, jid, password, agent_name):
        super().__init__(jid, password)
        self.agent_name = agent_name
        
        # --- ROBUST SSL FIX ---
        self.ssl_verify = False
        self.auto_start_tls = False
        self.use_tls = False
        self.use_ssl = False
        if hasattr(ssl, 'SSLContext'):
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        # --- END OF FIX ---
        
        # Event handlers
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message_received)
        self.add_event_handler("disconnected", self.on_disconnect)
        
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0199')

        # Game State
        self.players_jid = ["player1@localhost", "player2@localhost", "player3@localhost"]
        self.current_moves = {}
        self.round_count = 0
        self.max_rounds = 3
        self.scores = {jid: 0 for jid in self.players_jid}

    def start(self, event):
        """Called when the bot connects successfully"""
        self.send_presence()
        self.get_roster()
        
        logging.info(f"{self.agent_name} connected and ready!")
        
        # Evaluator Logic: Start the game
        if "evaluator" in self.boundjid.bare:
            # Wait 5 seconds for players to connect
            self.schedule('start_game', 5, self.start_new_round, repeat=False)
        else:
            logging.info(f"{self.agent_name} waiting for the Referee...")

    def start_new_round(self):
        """Evaluator starts a specific round"""
        if self.round_count < self.max_rounds:
            self.round_count += 1
            self.current_moves = {} # Reset moves for new round
            
            logging.info(f"--- STARTING ROUND {self.round_count} ---")
            msg = f"CMD:START_ROUND:{self.round_count}"
            
            # Broadcast to all players
            for player in self.players_jid:
                self.send_message(mto=player, mbody=msg, mtype='chat')
        else:
            self.declare_final_winner()

    def message_received(self, msg):
        """Handle incoming messages"""
        if msg['type'] in ('chat', 'normal'):
            sender = msg['from'].bare
            body = msg['body']

            if "evaluator" in self.boundjid.bare:
                self.handle_evaluator_logic(sender, body)
            else:
                asyncio.create_task(self.handle_player_logic(sender, body))

    # ---------------- EVALUATOR LOGIC ----------------
    def handle_evaluator_logic(self, sender, body):
        if body.startswith("MOVE:"):
            move = body.split(":")[1]
            logging.info(f"Evaluator received move from {sender}: {move}")
            
            # Record move
            self.current_moves[sender] = move
            
            # Check if all 3 players have played
            if len(self.current_moves) == len(self.players_jid):
                self.evaluate_round()

    def evaluate_round(self):
        """Determine logic for Rock Paper Scissors (3 Players)"""
        moves = self.current_moves
        # Logic:
        # Rock beats Scissors
        # Scissors beats Paper
        # Paper beats Rock
        
        unique_moves = set(moves.values())
        
        winners = []
        result_msg = ""

        # CASE 1: Draw (All 3 same OR All 3 different)
        # e.g. R, R, R or R, P, S
        if len(unique_moves) == 1 or len(unique_moves) == 3:
            result_msg = "Draw! No points awarded."
            logging.info(f"Round Result: {result_msg}")
        
        # CASE 2: Two types of moves present (Someone wins)
        else:
            # Determine which move wins
            winning_move = ""
            if 'rock' in unique_moves and 'scissors' in unique_moves:
                winning_move = 'rock'
            elif 'scissors' in unique_moves and 'paper' in unique_moves:
                winning_move = 'scissors'
            elif 'paper' in unique_moves and 'rock' in unique_moves:
                winning_move = 'paper'
            
            # Assign points
            for player, move in moves.items():
                if move == winning_move:
                    self.scores[player] += 1
                    winners.append(player)
            
            result_msg = f"Winners: {', '.join(winners)} with {winning_move}"
            logging.info(f"Round Result: {result_msg}")

        # Notify players of round result
        for player in self.players_jid:
            self.send_message(mto=player, mbody=f"RESULT:{result_msg}", mtype='chat')
            
        # Schedule next round
        asyncio.get_event_loop().call_later(2, self.start_new_round)

    def declare_final_winner(self):
        """End of game logic"""
        logging.info("--- GAME OVER ---")
        logging.info(f"Final Scores: {self.scores}")
        
        # Find max score
        max_score = max(self.scores.values())
        winners = [p for p, s in self.scores.items() if s == max_score]
        
        final_msg = ""
        if len(winners) == 1:
            final_msg = f"FINAL WINNER: {winners[0]} with {max_score} points!"
        else:
            final_msg = f"FINAL DRAW between: {', '.join(winners)} with {max_score} points!"
            
        logging.info(final_msg)
        for player in self.players_jid:
            self.send_message(mto=player, mbody=f"FINAL:{final_msg}", mtype='chat')

    # ---------------- PLAYER LOGIC ----------------
    async def handle_player_logic(self, sender, body):
        if body.startswith("CMD:START_ROUND"):
            round_num = body.split(":")[2]
            logging.info(f"{self.agent_name} starting Round {round_num}...")
            
            # Simulate thinking time
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Pick Move
            options = ['rock', 'paper', 'scissors']
            my_move = random.choice(options)
            
            logging.info(f"{self.agent_name} chose {my_move}")
            self.send_message(mto=sender, mbody=f"MOVE:{my_move}", mtype='chat')
            
        elif body.startswith("RESULT:"):
            res = body.split(":")[1]
            logging.info(f"{self.agent_name} saw result: {res}")
            
        elif body.startswith("FINAL:"):
            res = body.split(":")[1]
            logging.info(f"{self.agent_name} saw FINAL result: {res}")

    def on_disconnect(self, event):
        logging.info(f"{self.agent_name} disconnected")

def main():
    # Load environment variables
    jid = os.getenv('AGENT_JID')
    password = os.getenv('AGENT_PASSWORD')
    server = os.getenv('XMPP_SERVER', 'localhost')
    agent_name = os.getenv('AGENT_NAME')
    
    if not jid:
        print("Error: AGENT_JID not set")
        return

    agent = XMPPAgent(jid, password, agent_name)
    agent.connect((server, 5222))
    agent.process(forever=True)

if __name__ == '__main__':
    main()