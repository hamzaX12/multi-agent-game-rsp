import os
import logging
import asyncio
import ssl
import random  # Added for random bid generation
from slixmpp import ClientXMPP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

class XMPPAgent(ClientXMPP):
    def __init__(self, jid, password, agent_name):
        super().__init__(jid, password)
        self.agent_name = agent_name
        
        # --- ROBUST SSL FIX (Unchanged) ---
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
        
        # Negotiation State
        self.received_bids = {}
        self.expected_buyers = ["buyer@localhost", "buyer2@localhost"]

    def start(self, event):
        """Called when the bot connects successfully"""
        self.send_presence()
        self.get_roster()
        
        logging.info(f"{self.agent_name} connected and ready!")
        
        # If I am the Seller, I start the auction
        if "seller" in self.boundjid.bare:
            # Wait 5 seconds to ensure buyers are online/ready
            self.schedule('start_auction', 5, self.start_auction_sync, repeat=False)
        else:
            logging.info(f"{self.agent_name} is waiting for offers...")

    def start_auction_sync(self):
        asyncio.create_task(self.broadcast_offer())

    async def broadcast_offer(self):
        """Seller sends an offer to all buyers"""
        item = "Vintage Laptop"
        start_price = 100
        msg_body = f"OFFER:{item}:{start_price}"
        
        logging.info(f"--- {self.agent_name} STARTING AUCTION for {item} at ${start_price} ---")
        
        for buyer in self.expected_buyers:
            self.send_message(mto=buyer, mbody=msg_body, mtype='chat')
            logging.info(f"Sent offer to {buyer}")

    def message_received(self, msg):
        """Handle incoming messages"""
        if msg['type'] in ('chat', 'normal'):
            sender = msg['from'].bare
            body = msg['body']
            
            # SELLER LOGIC
            if "seller" in self.boundjid.bare:
                self.handle_seller_logic(sender, body)
            
            # BUYER LOGIC
            else:
                asyncio.create_task(self.handle_buyer_logic(sender, body))

    def handle_seller_logic(self, sender, body):
        if body.startswith("BID:"):
            try:
                bid_amount = int(body.split(":")[1])
                logging.info(f"Seller received BID from {sender}: ${bid_amount}")
                
                # Store the bid
                self.received_bids[sender] = bid_amount
                
                # Check if we have received bids from all expected buyers
                if len(self.received_bids) >= len(self.expected_buyers):
                    self.determine_winner()
            except ValueError:
                logging.error(f"Invalid bid format from {sender}")

    def determine_winner(self):
        """Calculate highest bid and notify agents"""
        if not self.received_bids:
            return

        # Find max bid
        winner_jid = max(self.received_bids, key=self.received_bids.get)
        winning_price = self.received_bids[winner_jid]
        
        logging.info(f"--- AUCTION ENDED. Winner: {winner_jid} with ${winning_price} ---")

        # Notify Winner
        self.send_message(mto=winner_jid, mbody="RESULT:WIN:You won the auction!", mtype='chat')
        
        # Notify Losers
        for loser in self.received_bids:
            if loser != winner_jid:
                self.send_message(mto=loser, mbody=f"RESULT:LOSE:Item sold to another for ${winning_price}", mtype='chat')
        
        # Reset for potential next round (optional)
        self.received_bids = {}

    async def handle_buyer_logic(self, sender, body):
        # Buyer receives an Offer
        if body.startswith("OFFER:"):
            parts = body.split(":")
            item = parts[1]
            base_price = int(parts[2])
            
            logging.info(f"{self.agent_name} received offer for {item} at ${base_price}")
            
            # Wait a moment to simulate thinking
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Generate a random bid (base price + 10 to 50)
            my_bid = base_price + random.randint(10, 50)
            
            reply = f"BID:{my_bid}"
            self.send_message(mto=sender, mbody=reply, mtype='chat')
            logging.info(f"{self.agent_name} placed bid: ${my_bid}")

        # Buyer receives Result
        elif body.startswith("RESULT:"):
            status = body.split(":")[1]
            message = body.split(":")[2]
            if status == "WIN":
                logging.info(f"🎉 {self.agent_name} WON! ({message})")
            else:
                logging.info(f"😞 {self.agent_name} LOST. ({message})")

    def on_disconnect(self, event):
        logging.info(f"{self.agent_name} disconnected")

def main():
    jid = os.getenv('AGENT_JID', 'seller@localhost')
    password = os.getenv('AGENT_PASSWORD', 'sellerpass')
    server = os.getenv('XMPP_SERVER', 'localhost')
    agent_name = os.getenv('AGENT_NAME', 'Seller')
    
    agent = XMPPAgent(jid, password, agent_name)
    agent.connect((server, 5222))
    agent.process(forever=True)

if __name__ == '__main__':
    main()