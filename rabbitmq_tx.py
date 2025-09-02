import logging
import json
import pika
import os
import ssl
from datetime import datetime
from typing import Dict, Optional

class MessageTransmitter:
    """
    A class to transmit messages composed of two text values from a dictionary,
    with RabbitMQ as the transmission endpoint and logging capabilities.
    """
    
    def __init__(self, log_file: Optional[str] = None, log_level: int = logging.INFO,
                 rabbitmq_host: str = 'localhost', rabbitmq_port: int = 5672,
                 rabbitmq_vhost: str = '/', queue_name: str = 'messages',
                 exchange_name: str = '', routing_key: str = '',
                 username: Optional[str] = None, password: Optional[str] = None,
                 use_ssl: bool = False):
        """
        Initialize the MessageTransmitter with secure RabbitMQ connection.
        
        Args:
            log_file (str, optional): Path to log file. If None, logs to console.
            log_level (int): Logging level (default: INFO)
            rabbitmq_host (str): RabbitMQ host address (default: 'localhost')
            rabbitmq_port (int): RabbitMQ port (default: 5672)
            rabbitmq_vhost (str): RabbitMQ virtual host (default: '/')
            queue_name (str): RabbitMQ queue name (default: 'messages')
            exchange_name (str): RabbitMQ exchange name (default: '' for default exchange)
            routing_key (str): Routing key for messages (default: '' uses queue_name)
            username (str, optional): Username for authentication (if None, checks env vars)
            password (str, optional): Password for authentication (if None, checks env vars)
            use_ssl (bool): Whether to use SSL/TLS connection (default: False)
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
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_vhost = rabbitmq_vhost
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.routing_key = routing_key or queue_name
        self.use_ssl = use_ssl
        
        # Secure credential handling
        self.username = username or os.getenv('RABBITMQ_USERNAME')
        self.password = password or os.getenv('RABBITMQ_PASSWORD')
        
        # Connection objects
        self.connection = None
        self.channel = None
        
        # Initialize RabbitMQ connection
        self._connect_to_rabbitmq()
    
    def _connect_to_rabbitmq(self):
        """Establish secure connection to RabbitMQ and declare queue."""
        try:
            # Create connection parameters
            credentials = None
            if self.username and self.password:
                credentials = pika.PlainCredentials(self.username, self.password)
                self.logger.info(f"Using credentials for user: {self.username}")
            else:
                self.logger.info("No credentials provided, using guest access or external auth")
            
            # Configure SSL if requested
            ssl_options = None
            if self.use_ssl:
                # Create a default SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False  # Disable hostname verification for development
                ssl_options = pika.SSLOptions(ssl_context)
                self.logger.info("SSL/TLS enabled for RabbitMQ connection")
            
            # Create connection parameters
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                virtual_host=self.rabbitmq_vhost,
                credentials=credentials,
                ssl_options=ssl_options,
                heartbeat=600,  # Heartbeat every 10 minutes
                blocked_connection_timeout=300  # 5 minute timeout
            )
            
            # Establish connection
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (create if it doesn't exist)
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            protocol = "amqps" if self.use_ssl else "amqp"
            self.logger.info(f"Connected to RabbitMQ at {protocol}://{self.rabbitmq_host}:{self.rabbitmq_port}")
            self.logger.info(f"Queue '{self.queue_name}' declared")
            
        except pika.exceptions.ProbableAuthenticationError as e:
            self.logger.error(f"Authentication failed - check username/password: {str(e)}")
            raise
        except pika.exceptions.ProbableAccessDeniedError as e:
            self.logger.error(f"Access denied - check user permissions: {str(e)}")
            raise
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
    # Example 1: Using environment variables (recommended)
    # Set these in your environment or .env file:
    # export RABBITMQ_USERNAME=myuser
    # export RABBITMQ_PASSWORD=mypassword
    
    print("Example 1: Using environment variables")
    try:
        transmitter = MessageTransmitter(
            log_file="message_log.txt",
            rabbitmq_host='localhost',
            rabbitmq_port=5672,
            queue_name='secure_message_queue',
            use_ssl=False  # Set to True for production
        )
        
        # Example message data
        sample_message = {
            "sender": "Alice",
            "recipient": "Bob", 
            "subject": "Meeting Request",
            "body": "Can we schedule a meeting for tomorrow?"
        }
        
        # Transmit single message to RabbitMQ
        result = transmitter.transmit_message(sample_message, "sender", "subject")
        print("Message transmitted to RabbitMQ:", result['combined_message'])
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'transmitter' in locals():
            transmitter.close_connection()
    
    # Example 2: Using direct parameters (less secure, avoid in production)
    print("\nExample 2: Direct parameter passing (development only)")
    try:
        with MessageTransmitter(
            rabbitmq_host='localhost',
            rabbitmq_port=5672,
            queue_name='test_queue',
            username='testuser',  # Better to use env vars
            password='testpass',  # Better to use env vars
            use_ssl=False
        ) as transmitter:
            
            batch_messages = [
                {"title": "Alert", "content": "System update required"},
                {"title": "Notification", "content": "New user registered"},
                {"title": "Warning", "content": "Low disk space detected"}
            ]
            
            batch_results = transmitter.batch_transmit(batch_messages, "title", "content")
            print(f"Batch transmission completed: {len(batch_results)} messages sent to RabbitMQ")
            
    except Exception as e:
        print(f"Context manager error: {e}")
    
    # Example 3: Production-like configuration with SSL
    print("\nExample 3: Production configuration with SSL")
    print("# To use in production, set these environment variables:")
    print("# export RABBITMQ_USERNAME=prod_user")
    print("# export RABBITMQ_PASSWORD=secure_password")
    print("# export RABBITMQ_HOST=rabbitmq.example.com")
    print("# export RABBITMQ_PORT=5671")
    
    production_config_example = """
    # Production usage example:
    transmitter = MessageTransmitter(
        log_file="/var/log/message_transmitter.log",
        rabbitmq_host=os.getenv('RABBITMQ_HOST', 'localhost'),
        rabbitmq_port=int(os.getenv('RABBITMQ_PORT', 5671)),
        queue_name='production_messages',
        use_ssl=True,
        # username and password automatically read from env vars
    )
    """
    print(production_config_example)
