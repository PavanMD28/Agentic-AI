from flask import Flask, Response
from threading import Thread
from typing import List, Optional
import json
from datetime import datetime
import time
import uuid
from models import MessageContext, F1Standings, Driver

class FastMCPSSEServer:
    """
    SSE Server implementation with FastMCP protocol integration.
    Provides real-time F1 standings updates with MCP compliance.
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.latest_standings: Optional[MessageContext] = None
        self.setup_routes()

    def create_message_context(self, standings_data: List[dict]) -> MessageContext:
        """
        Creates an MCP-compliant message context from standings data.
        """
        trace_id = str(uuid.uuid4())  # Create a single trace_id for the entire context
        
        drivers = [
            Driver(
                position=standing['position'],
                driver_name=standing['driver'],
                points=standing['points'],
                trace_id=trace_id,  # Use the same trace_id for consistency
                mcp_version="1.0"
            ) for standing in standings_data
        ]
        
        f1_standings = F1Standings(
            timestamp=datetime.now(),
            standings=drivers,
            last_updated=datetime.now(),
            trace_id=trace_id,  # Use the same trace_id
            metadata={"update_type": "real_time"},
            mcp_version="1.0"
        )
        
        return MessageContext(
            message_id=str(uuid.uuid4()),
            message_type="F1_STANDINGS_UPDATE",
            content=f1_standings,
            trace_id=trace_id,  # Use the same trace_id
            metadata={
                "processing_timestamp": datetime.now().isoformat(),
                "source_system": "F1_API"
            },
            mcp_version="1.0"
        )

    def event_stream(self):
        """
        Generates SSE stream with MCP-compliant messages.
        """
        while True:
            if self.latest_standings and self.latest_standings.validate_mcp_compliance():
                data = {
                    "data": self.latest_standings.model_dump(),
                    "trace_context": self.latest_standings.get_trace_context()
                }
                yield f"data: {json.dumps(data)}\n\n"
            time.sleep(30)  # Reduced from 60 to 30 for faster updates

    def setup_routes(self):
        """
        Sets up Flask routes with FastMCP validation.
        """
        @self.app.route('/stream')
        def stream():
            return Response(self.event_stream(), mimetype="text/event-stream")

        @self.app.route('/standings')
        def get_standings():
            if self.latest_standings and self.latest_standings.validate_mcp_compliance():
                return self.latest_standings.model_dump_json()
            return json.dumps({"error": "No valid standings available"})

    def update_standings(self, standings: List[dict]) -> MessageContext:
        """
        Updates standings with MCP validation.
        """
        message_context = self.create_message_context(standings)
        if message_context.validate_mcp_compliance():
            self.latest_standings = message_context
        return self.latest_standings

    def start(self, host='localhost', port=5000):
        """
        Starts the SSE server with FastMCP integration.
        """
        def run_server():
            self.app.run(host=host, port=port, threaded=True)
        
        server_thread = Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

# Global server instance
sse_server = FastMCPSSEServer()

# Helper functions for backward compatibility
def start_sse_server():
    sse_server.start()

def update_standings(standings):
    return sse_server.update_standings(standings)