import logging
import json
import pika
import os
import ssl
from datetime import datetime
from typing import Dict, Optional

class MessageTransmitter:
    """
    A class to transmit messages composed of any number of key-value pairs from a dictionary,
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
            message_body = json.dumps(message, indent=2, default=str)  # default=str handles non-serializable types
            
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
    
    def transmit_message(self, message_data: Dict) -> Dict:
        """
        Transmit a message containing all key-value pairs from the dictionary to RabbitMQ.
        
        Args:
            message_data (Dict): Dictionary containing message data with any number of key-value pairs
        
        Returns:
            Dict: Dictionary containing the transmitted message with timestamp and metadata
            
        Raises:
            ValueError: If message_data is empty or not a dictionary
        """
        try:
            # Validate input
            if not isinstance(message_data, dict):
                raise ValueError("message_data must be a dictionary")
            
            if not message_data:
                raise ValueError("message_data cannot be empty")
            
            # Create a copy of the original data to avoid modifying the input
            composed_message = message_data.copy()
            
            # Add transmission metadata
            composed_message['_timestamp'] = datetime.now().isoformat()
            composed_message['_message_id'] = f"msg_{int(datetime.now().timestamp() * 1000)}"
            composed_message['_total_fields'] = len(message_data)
            
            # Create summary of all key-value pairs for logging
            field_summary = []
            for key, value in message_data.items():
                # Convert all values to strings for consistent handling
                str_value = str(value)
                field_summary.append(f"{key}: '{str_value[:50]}{'...' if len(str_value) > 50 else ''}'")
            
            # Log the transmission with field summary
            self.logger.info(f"Message composed with {len(message_data)} fields: {', '.join(field_summary[:5])}")
            if len(field_summary) > 5:
                self.logger.info(f"... and {len(field_summary) - 5} more fields")
            
            # Transmit to RabbitMQ
            success = self._publish_to_rabbitmq(composed_message)
            
            if success:
                self.logger.info(f"Message successfully transmitted to RabbitMQ (ID: {composed_message['_message_id']})")
            else:
                self.logger.error("Failed to transmit message to RabbitMQ")
                raise RuntimeError("Message transmission to RabbitMQ failed")
            
            return composed_message
            
        except Exception as e:
            self.logger.error(f"Failed to transmit message: {str(e)}")
            raise
    
    def batch_transmit(self, messages: list[Dict]) -> list[Dict]:
        """
        Transmit multiple messages in batch to RabbitMQ.
        
        Args:
            messages (list[Dict]): List of message dictionaries with any number of key-value pairs
        
        Returns:
            list[Dict]: List of transmitted messages
        """
        transmitted_messages = []
        
        self.logger.info(f"Starting batch transmission of {len(messages)} messages")
        
        for i, message_data in enumerate(messages):
            try:
                transmitted_msg = self.transmit_message(message_data)
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
        
        # Example message data with multiple fields
        sample_message = {
            "sender": "Alice",
            "recipient": "Bob", 
            "subject": "Meeting Request",
            "body": "Can we schedule a meeting for tomorrow?",
            "priority": "high",
            "department": "Engineering",
            "project": "Q1 Planning"
        }
        
        # Transmit single message to RabbitMQ
        result = transmitter.transmit_message(sample_message)
        print("Message transmitted to RabbitMQ:", result['_message_id'])
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'transmitter' in locals():
            transmitter.close_connection()
    
    # Example 2: Using direct parameters (less secure, avoid in production)
    print("\nExample 2: Direct parameter passing with flexible message structure")
    try:
        with MessageTransmitter(
            rabbitmq_host='localhost',
            rabbitmq_port=5672,
            queue_name='test_queue',
            username='testuser',  # Better to use env vars
            password='testpass',  # Better to use env vars
            use_ssl=False
        ) as transmitter:
            
            # Batch messages with different structures
            batch_messages = [
                {"title": "Alert", "content": "System update required", "priority": "high", "department": "IT"},
                {"title": "Notification", "content": "New user registered", "user_id": 12345, "email": "user@example.com"},
                {"title": "Warning", "content": "Low disk space detected", "server": "web-01", "usage": "85%", "threshold": "80%"}
            ]
            
            batch_results = transmitter.batch_transmit(batch_messages)
            print(f"Batch transmission completed: {len(batch_results)} messages sent to RabbitMQ")
            
    except Exception as e:
        print(f"Context manager error: {e}")
    
    # Example 3: Complex message with various data types
    print("\nExample 3: Complex message with various data types")
    try:
        with MessageTransmitter(
            rabbitmq_host='localhost',
            queue_name='complex_messages'
        ) as transmitter:
            
            complex_message = {
                "event_type": "user_action",
                "user_id": 12345,
                "timestamp": datetime.now(),
                "metadata": {
                    "browser": "Chrome",
                    "version": "91.0"
                },
                "tags": ["important", "user", "action"],
                "score": 85.7,
                "active": True
            }
            
            result = transmitter.transmit_message(complex_message)
            print(f"Complex message transmitted: {result['_message_id']}")
            
    except Exception as e:
        print(f"Complex message error: {e}")
    
    # Example 4: Production-like configuration with SSL
    print("\nExample 4: Production configuration with SSL")
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
