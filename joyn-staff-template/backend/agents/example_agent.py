"""
Example Agent Structure
========================
Use this as a starting point for your agent logic.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AgentInput:
    """Standard input structure for agents."""
    client_id: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@dataclass
class AgentOutput:
    """Standard output structure for agents."""
    success: bool
    output_type: str
    content: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseAgent:
    """
    Base class for all Joyn AI staff agents.
    
    Implement the `process` method with your logic.
    """
    
    def __init__(self, name: str, client_id: str):
        self.name = name
        self.client_id = client_id
        self.logger = logging.getLogger(f"agent.{name}")
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Main processing logic. Override this method.
        
        Args:
            input_data: The input to process
            
        Returns:
            AgentOutput with results
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """
        Validate input before processing.
        Override for custom validation.
        """
        if not input_data.client_id:
            self.logger.error("Missing client_id")
            return False
        if not input_data.data:
            self.logger.error("Missing data")
            return False
        return True
    
    def handle_failure(self, error: Exception, input_data: AgentInput) -> AgentOutput:
        """
        Handle processing failures gracefully.
        Override for custom failure handling.
        """
        self.logger.error(f"Processing failed: {error}", exc_info=True)
        return AgentOutput(
            success=False,
            output_type="error",
            content={
                "error": str(error),
                "input_received": str(input_data.data)[:100],
                "timestamp": datetime.utcnow().isoformat()
            },
            confidence=0.0
        )
    
    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent with standard error handling.
        Do not override this method.
        """
        self.logger.info(f"Starting {self.name} for client {input_data.client_id}")
        
        # Validate input
        if not self.validate_input(input_data):
            return AgentOutput(
                success=False,
                output_type="validation_error",
                content={"error": "Input validation failed"},
                confidence=0.0
            )
        
        # Process
        try:
            result = self.process(input_data)
            self.logger.info(f"Completed {self.name}: success={result.success}")
            return result
        except Exception as e:
            return self.handle_failure(e, input_data)


class ExampleMonitorAgent(BaseAgent):
    """
    Example: A monitoring agent that checks for updates.
    
    Replace this with your actual agent logic.
    """
    
    def __init__(self, client_id: str):
        super().__init__("Monitor", client_id)
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Example monitoring logic.
        """
        # Get monitoring configuration
        sources = input_data.data.get("sources", [])
        keywords = input_data.data.get("keywords", [])
        
        # Simulate monitoring (replace with real logic)
        findings = []
        for source in sources:
            # In reality, you'd fetch and analyze the source
            findings.append({
                "source": source,
                "status": "checked",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return AgentOutput(
            success=True,
            output_type="monitoring_result",
            content={
                "sources_checked": len(sources),
                "findings": findings,
                "next_check": "in 1 hour"
            },
            confidence=0.95  # High confidence as this is a deterministic check
        )


class ExampleAnalysisAgent(BaseAgent):
    """
    Example: An analysis agent that processes data.
    
    Replace this with your actual agent logic.
    """
    
    def __init__(self, client_id: str):
        super().__init__("Analyst", client_id)
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Example analysis logic.
        """
        document = input_data.data.get("document", "")
        
        if not document:
            return AgentOutput(
                success=False,
                output_type="analysis_error",
                content={"error": "No document provided"},
                confidence=0.0
            )
        
        # Simulate analysis (replace with real logic)
        word_count = len(document.split())
        
        # Confidence based on input quality
        confidence = min(1.0, word_count / 100)  # Example: more text = more confidence
        
        return AgentOutput(
            success=True,
            output_type="analysis_result",
            content={
                "word_count": word_count,
                "summary": document[:200] + "..." if len(document) > 200 else document,
                "key_findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1"]
            },
            confidence=confidence
        )


# Usage example
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent
    monitor = ExampleMonitorAgent(client_id="test-client-123")
    
    # Create input
    input_data = AgentInput(
        client_id="test-client-123",
        data={
            "sources": ["https://example.com/feed1", "https://example.com/feed2"],
            "keywords": ["regulation", "compliance"]
        }
    )
    
    # Run agent
    result = monitor.run(input_data)
    print(f"Result: {result}")
