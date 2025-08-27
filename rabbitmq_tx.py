import logging
import json
import pika
from datetime import datetime
from typing import Dict, Optional

"""
I've updated the code to use RabbitMQ as the transmission endpoint. Here are the key changes and new features:

New Dependencies:

Added pika library for RabbitMQ communication
Added json for message serialization
RabbitMQ Integration:

Connection Management: Automatic connection to RabbitMQ with configurable URL
Queue Declaration: Creates durable queues if they don't exist
Message Publishing: Messages are published as JSON with persistence
Connection Recovery: Automatically reconnects if connection is lost
New Configuration Options:

rabbitmq_url: RabbitMQ server URL (default: 'amqp://localhost')
queue_name: Target queue name (default: 'messages')
exchange_name: Exchange to use (default: '' for default exchange)
routing_key: Message routing key (defaults to queue_name)
Enhanced Features:

Context Manager Support: Use with statement for automatic connection cleanup
Persistent Messages: Messages survive RabbitMQ server restarts
JSON Serialization: Messages are automatically converted to JSON format
Connection Lifecycle: Proper connection opening/closing with error handling
Installation Requirements:

bash
pip install pika
Basic Usage:

python
# Initialize with RabbitMQ settings
transmitter = MessageTransmitter(
    rabbitmq_url='amqp://guest:guest@localhost:5672/',
    queue_name='my_queue'
)

# Messages are now published to RabbitMQ
result = transmitter.transmit_message(data, "key1", "key2")
The class now acts as a bridge between your dictionary data and RabbitMQ, maintaining all the original logging functionality while adding robust message queue transmission capabilities.
"""

class MessageTransmitter:
    """
    A class to transmit messages composed of two text values from a dictionary,
    with RabbitMQ as the transmission endpoint and logging capabilities.
    """
    
    def __init__(self, log_file: Optional[str] = None, log_level: int = logging.INFO,
                 rabbitmq_url: str = 'amqp://localhost', queue_name: str = 'messages',
                 exchange_name: str = '', routing_key: str = ''):
        """
        Initialize the MessageTransmitter with RabbitMQ connection.
        
        Args:
            log_file (str, optional): Path to log file. If None, logs to console.
            log_level (int): Logging level (default: INFO)
            rabbitmq_url (str): RabbitMQ connection URL (default: 'amqp://localhost')
            queue_name (str): RabbitMQ queue name (default: 'messages')
            exchange_name (str): RabbitMQ exchange name (default: '' for default exchange)
            routing_key (str): Routing key for messages (default: '' uses queue_name)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter with date and time
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configure handler (file or console)
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # RabbitMQ configuration
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.routing_key = routing_key or queue_name
        self.connection = None
        self.channel = None
        
        # Initialize RabbitMQ connection
        self._connect_to_rabbitmq()
    
    def _connect_to_rabbitmq(self):
        """Establish connection to RabbitMQ and declare queue."""
        try:
            # Parse connection URL and create connection
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (create if it doesn't exist)
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            self.logger.info(f"Connected to RabbitMQ at {self.rabbitmq_url}")
            self.logger.info(f"Queue '{self.queue_name}' declared")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    def _publish_to_rabbitmq(self, message: Dict) -> bool:
        """
        Publish message to RabbitMQ queue.
        
        Args:
            message (Dict): Message to publish
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Ensure connection is active
            if not self.connection or self.connection.is_closed:
                self._connect_to_rabbitmq()
            
            # Convert message to JSON string
            message_body = json.dumps(message, indent=2)
            
            # Publish message
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json',
                    timestamp=int(datetime.now().timestamp())
                )
            )
            
            self.logger.info(f"Message published to RabbitMQ queue '{self.queue_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish message to RabbitMQ: {str(e)}")
            return False
    
    def close_connection(self):
        """Close the RabbitMQ connection."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                self.logger.info("RabbitMQ connection closed")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close_connection()
    
    def transmit_message(self, message_data: Dict[str, str], 
                        key1: str, key2: str) -> Dict[str, str]:
        """
        Transmit a message composed of two text values from a dictionary to RabbitMQ.
        
        Args:
            message_data (Dict[str, str]): Dictionary containing message data
            key1 (str): First key to extract from dictionary
            key2 (str): Second key to extract from dictionary
        
        Returns:
            Dict[str, str]: Dictionary containing the transmitted message
            
        Raises:
            KeyError: If required keys are not found in message_data
            ValueError: If extracted values are not strings
        """
        try:
            # Extract values from dictionary
            if key1 not in message_data:
                raise KeyError(f"Key '{key1}' not found in message data")
            if key2 not in message_data:
                raise KeyError(f"Key '{key2}' not found in message data")
            
            value1 = message_data[key1]
            value2 = message_data[key2]
            
            # Validate that values are strings
            if not isinstance(value1, str) or not isinstance(value2, str):
                raise ValueError("Both values must be strings")
            
            # Compose the message
            composed_message = {
                'timestamp': datetime.now().isoformat(),
                key1: value1,
                key2: value2,
                'combined_message': f"{value1} | {value2}"
            }
            
            # Log the transmission
            self.logger.info(
                f"Message composed - {key1}: '{value1}', {key2}: '{value2}'"
            )
            
            # Transmit to RabbitMQ
            success = self._publish_to_rabbitmq(composed_message)
            
            if success:
                self.logger.info("Message successfully transmitted to RabbitMQ")
            else:
                self.logger.error("Failed to transmit message to RabbitMQ")
                raise RuntimeError("Message transmission to RabbitMQ failed")
            
            return composed_message
            
        except Exception as e:
            self.logger.error(f"Failed to transmit message: {str(e)}")
            raise
    
    def batch_transmit(self, messages: list[Dict[str, str]], 
                      key1: str, key2: str) -> list[Dict[str, str]]:
        """
        Transmit multiple messages in batch to RabbitMQ.
        
        Args:
            messages (list[Dict[str, str]]): List of message dictionaries
            key1 (str): First key to extract from each dictionary
            key2 (str): Second key to extract from each dictionary
        
        Returns:
            list[Dict[str, str]]: List of transmitted messages
        """
        transmitted_messages = []
        
        self.logger.info(f"Starting batch transmission of {len(messages)} messages")
        
        for i, message_data in enumerate(messages):
            try:
                transmitted_msg = self.transmit_message(message_data, key1, key2)
                transmitted_messages.append(transmitted_msg)
            except Exception as e:
                self.logger.error(f"Failed to transmit message {i+1}: {str(e)}")
                continue
        
        self.logger.info(f"Batch transmission completed. {len(transmitted_messages)}/{len(messages)} messages sent successfully to RabbitMQ")
        return transmitted_messages


# Example usage
if __name__ == "__main__":
    # Create transmitter instance with RabbitMQ configuration
    transmitter = MessageTransmitter(
        log_file="message_log.txt",
        rabbitmq_url='amqp://guest:guest@localhost:5672/',
        queue_name='message_queue',
        exchange_name='',
        routing_key='message_queue'
    )
    
    try:
        # Example message data
        sample_message = {
            "sender": "Alice",
            "recipient": "Bob", 
            "subject": "Meeting Request",
            "body": "Can we schedule a meeting for tomorrow?"
        }
        
        # Transmit single message to RabbitMQ
        result = transmitter.transmit_message(sample_message, "sender", "subject")
        print("Message transmitted to RabbitMQ:", result)
        
        # Example batch transmission
        batch_messages = [
            {"title": "Alert", "content": "System update required"},
            {"title": "Notification", "content": "New user registered"},
            {"title": "Warning", "content": "Low disk space detected"}
        ]
        
        batch_results = transmitter.batch_transmit(batch_messages, "title", "content")
        print(f"Batch transmission completed: {len(batch_results)} messages sent to RabbitMQ")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always close the connection
        transmitter.close_connection()
    
    # Alternative usage with context manager (automatically closes connection)
    print("\nUsing context manager:")
    try:
        with MessageTransmitter(
            rabbitmq_url='amqp://guest:guest@localhost:5672/',
            queue_name='test_queue'
        ) as transmitter:
            message = {"type": "test", "data": "Hello RabbitMQ!"}
            result = transmitter.transmit_message(message, "type", "data")
            print("Context manager transmission successful")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example batch transmission
    batch_messages = [
        {"title": "Alert", "content": "System update required"},
        {"title": "Notification", "content": "New user registered"},
        {"title": "Warning", "content": "Low disk space detected"}
    ]
    
    batch_results = transmitter.batch_transmit(batch_messages, "title", "content")
    print(f"Batch transmission completed: {len(batch_results)} messages sent")
