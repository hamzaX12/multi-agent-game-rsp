import os
import logging
import asyncio
import ssl  # Required for the robust SSL bypass fix
from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

# Configure logging for clear output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class XMPPAgent(ClientXMPP):
    def __init__(self, jid, password, agent_name):
        super().__init__(jid, password)
        self.agent_name = agent_name
        self.target_jid = None
        
        # --- ROBUST SSL FIX ---
        # 1. Standard slixmpp flags to disable verification (kept for completeness)
        self.ssl_verify = False
        self.auto_start_tls = False
        self.use_tls = False
        self.use_ssl = False
        
        # 2. Aggressive fix: Create and assign an SSL context that explicitly
        #    bypasses verification. This works even when the high-level flags fail.
        if hasattr(ssl, 'SSLContext'):
            # Use PROTOCOL_TLS_CLIENT for modern Python versions
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # CRITICAL FIX: Disable hostname check BEFORE setting verify_mode to CERT_NONE
            # Do not check hostname against the certificate (important for "localhost")
            self.ssl_context.check_hostname = False
            
            # Do not verify the certificate chain
            self.ssl_context.verify_mode = ssl.CERT_NONE
        # --- END OF FIX ---
        
        # Event handlers
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message_received)
        self.add_event_handler("disconnected", self.on_disconnect)
        
        # Register the bot
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # XMPP Ping
        
        self.messages_sent = 0

    def start(self, event):
        """Called when the bot connects successfully"""
        self.send_presence()
        self.get_roster()
        
        logging.info(f"{self.agent_name} connected and ready!")
        
        # Determine target based on which agent this is
        if "agent1" in self.boundjid.bare:
            self.target_jid = "agent2@localhost"
            # Agent1 initiates conversation - schedule it
            self.schedule('greeting', 2, self.send_greeting_sync, repeat=False)
        else:
            self.target_jid = "agent1@localhost"
            logging.info(f"{self.agent_name} waiting for messages from {self.target_jid}")

    async def send_greeting(self):
        """Send a greeting message"""
        if self.messages_sent < 3:  # Limit to 3 messages each
            message = f"Hi! This is {self.agent_name} saying hello! (Message #{self.messages_sent + 1})"
            self.send_message(mto=self.target_jid, mbody=message, mtype='chat')
            logging.info(f"{self.agent_name} sent: {message}")
            self.messages_sent += 1

    def send_greeting_sync(self):
        """Synchronous wrapper for send_greeting"""
        asyncio.create_task(self.send_greeting())

    def message_received(self, msg):
        """Handle incoming messages"""
        if msg['type'] in ('chat', 'normal'):
            sender = msg['from'].bare
            body = msg['body']
            
            logging.info(f"{self.agent_name} received from {sender}: {body}")
            
            # Reply back if we haven't sent too many messages
            if self.messages_sent < 3:
                asyncio.create_task(self.send_reply(sender))

    async def send_reply(self, to_jid):
        """Send a reply message"""
        await asyncio.sleep(1)  # Small delay to make conversation feel natural
        
        message = f"Hi back! {self.agent_name} received your message! (Reply #{self.messages_sent + 1})"
        self.send_message(mto=to_jid, mbody=message, mtype='chat')
        logging.info(f"{self.agent_name} replied: {message}")
        self.messages_sent += 1

    def on_disconnect(self, event):
        """Handle disconnection"""
        logging.info(f"{self.agent_name} disconnected")

def main():
    # Get configuration from environment variables
    jid = os.getenv('AGENT_JID', 'agent1@localhost')
    password = os.getenv('AGENT_PASSWORD', 'agent1pass')
    server = os.getenv('XMPP_SERVER', 'localhost')
    agent_name = os.getenv('AGENT_NAME', 'Agent1')
    
    logging.info(f"Starting {agent_name} with JID: {jid}")
    
    # Create and configure the agent
    agent = XMPPAgent(jid, password, agent_name)
    
    # Connect to the server
    agent.connect((server, 5222))
    
    # Process events - this runs its own event loop
    agent.process(forever=True)


if __name__ == '__main__':
    main()