import logging
import json
import pika
import os
import ssl
from datetime import datetime
from typing import Dict, Optional, Callable
from pathlib import Path
import threading
import time


class EnhancedMessageTransmitter:
    """
    Enhanced message transmitter with RabbitMQ fallback to file storage
    when RabbitMQ service is unavailable
    """
    
    def __init__(self, log_file: Optional[str] = None, log_level: int = logging.INFO,
                 rabbitmq_host: str = 'localhost', rabbitmq_port: int = 5672,
                 rabbitmq_vhost: str = '/', queue_name: str = 'messages',
                 exchange_name: str = '', routing_key: str = '',
                 username: Optional[str] = None, password: Optional[str] = None,
                 use_ssl: bool = False, fallback_file_dir: str = "rabbitmq_fallback",
                 connection_timeout: float = 5.0, retry_interval: float = 30.0,
                 status_callback: Optional[Callable[[bool], None]] = None):
        """
        Initialize the Enhanced MessageTransmitter with fallback capabilities.
        
        Args:
            log_file (str, optional): Path to log file. If None, logs to console.
            log_level (int): Logging level (default: INFO)
            rabbitmq_host (str): RabbitMQ host address (default: 'localhost')
            rabbitmq_port (int): RabbitMQ port (default: 5672)
            rabbitmq_vhost (str): RabbitMQ virtual host (default: '/')
            queue_name (str): RabbitMQ queue name (default: 'messages')
            exchange_name (str): RabbitMQ exchange name (default: '' for default exchange)
            routing_key (str): Routing key for messages (default: '' uses queue_name)
            username (str, optional): Username for authentication
            password (str, optional): Password for authentication
            use_ssl (bool): Whether to use SSL/TLS connection (default: False)
            fallback_file_dir (str): Directory for fallback message files
            connection_timeout (float): Timeout for connection attempts
            retry_interval (float): Interval between connection retry attempts
            status_callback (callable): Callback function called when connection status changes
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
        self.connection_timeout = connection_timeout
        self.retry_interval = retry_interval
        
        # Secure credential handling
        self.username = username or os.getenv('RABBITMQ_USERNAME')
        self.password = password or os.getenv('RABBITMQ_PASSWORD')
        
        # Connection objects and status
        self.connection = None
        self.channel = None
        self.connected = False
        self.status_callback = status_callback
        
        # Fallback configuration
        self.fallback_file_dir = Path(fallback_file_dir)
        self.fallback_file_dir.mkdir(exist_ok=True)
        self.fallback_file_path = self.fallback_file_dir / f"{self.queue_name}_messages.json"
        
        # Background connection monitoring
        self._stop_monitoring = False
        self._monitor_thread = None
        
        # Initialize RabbitMQ connection
        self._connect_to_rabbitmq()
        
        # Start connection monitoring
        self._start_connection_monitoring()
    
    def _connect_to_rabbitmq(self):
        """Attempt to establish connection to RabbitMQ."""
        try:
            # Create connection parameters
            credentials = None
            if self.username and self.password:
                credentials = pika.PlainCredentials(self.username, self.password)
                self.logger.debug(f"Using credentials for user: {self.username}")
            
            # Configure SSL if requested
            ssl_options = None
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_options = pika.SSLOptions(ssl_context)
                self.logger.debug("SSL/TLS enabled for RabbitMQ connection")
            
            # Create connection parameters with timeout
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                virtual_host=self.rabbitmq_vhost,
                credentials=credentials,
                ssl_options=ssl_options,
                heartbeat=600,
                blocked_connection_timeout=self.connection_timeout,
                socket_timeout=self.connection_timeout
            )
            
            # Establish connection
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (create if it doesn't exist)
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            protocol = "amqps" if self.use_ssl else "amqp"
            self.logger.info(f"Connected to RabbitMQ at {protocol}://{self.rabbitmq_host}:{self.rabbitmq_port}")
            self.logger.info(f"Queue '{self.queue_name}' declared")
            
            # Update connection status
            if not self.connected:
                self.connected = True
                self.logger.info("RabbitMQ connection established - switching from fallback mode")
                if self.status_callback:
                    self.status_callback(True)
                
                # Process any queued fallback messages
                self._process_fallback_messages()
            
        except Exception as e:
            if self.connected:
                self.logger.error(f"Lost connection to RabbitMQ: {str(e)}")
                self.connected = False
                if self.status_callback:
                    self.status_callback(False)
            else:
                self.logger.warning(f"Unable to connect to RabbitMQ: {str(e)}")
                self.logger.info("Operating in fallback mode - messages will be stored locally")
            
            self.connection = None
            self.channel = None
    
    def _start_connection_monitoring(self):
        """Start background thread to monitor and retry RabbitMQ connection."""
        def monitor_connection():
            while not self._stop_monitoring:
                if not self.is_connected():
                    self.logger.debug("Attempting to reconnect to RabbitMQ...")
                    self._connect_to_rabbitmq()
                
                # Wait before next check
                for _ in range(int(self.retry_interval)):
                    if self._stop_monitoring:
                        break
                    time.sleep(1)
        
        self._monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        self._monitor_thread.start()
        self.logger.debug("Connection monitoring started")
    
    def is_connected(self) -> bool:
        """
        Check if RabbitMQ connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connection or self.connection.is_closed:
            self.connected = False
            return False
        
        try:
            # Test connection with a heartbeat
            self.connection.process_data_events(time_limit=0)
            return True
        except Exception:
            self.connected = False
            return False
    
    def _publish_to_rabbitmq(self, message: Dict) -> bool:
        """
        Publish message to RabbitMQ queue.
        
        Args:
            message (Dict): Message to publish
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Check connection status
            if not self.is_connected():
                return False
            
            # Convert message to JSON string
            message_body = json.dumps(message, indent=2, default=str)
            
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
            self.connected = False
            if self.status_callback:
                self.status_callback(False)
            return False
    
    def _save_to_fallback_file(self, message: Dict) -> bool:
        """
        Save message to fallback file when RabbitMQ is unavailable.
        
        Args:
            message (Dict): Message to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Load existing messages
            messages = []
            if self.fallback_file_path.exists():
                try:
                    with open(self.fallback_file_path, 'r') as f:
                        messages = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning("Corrupted fallback file, starting fresh")
                    messages = []
            
            # Add new message with fallback metadata
            fallback_message = {
                "original_message": message,
                "fallback_timestamp": datetime.now().isoformat(),
                "fallback_reason": "rabbitmq_unavailable",
                "queue_name": self.queue_name,
                "routing_key": self.routing_key
            }
            
            messages.append(fallback_message)
            
            # Save back to file
            with open(self.fallback_file_path, 'w') as f:
                json.dump(messages, f, indent=2, default=str)
            
            self.logger.info(f"Message saved to fallback file: {self.fallback_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save message to fallback file: {str(e)}")
            return False
    
    def _process_fallback_messages(self):
        """Process any queued fallback messages when connection is restored."""
        if not self.fallback_file_path.exists():
            return
        
        try:
            with open(self.fallback_file_path, 'r') as f:
                fallback_messages = json.load(f)
            
            if not fallback_messages:
                return
            
            self.logger.info(f"Processing {len(fallback_messages)} fallback messages...")
            
            processed_count = 0
            for fallback_message in fallback_messages:
                original_message = fallback_message.get("original_message", {})
                
                # Try to send the original message
                if self._publish_to_rabbitmq(original_message):
                    processed_count += 1
                else:
                    # If we can't send, stop processing and keep remaining messages
                    break
            
            if processed_count > 0:
                # Remove processed messages from fallback file
                remaining_messages = fallback_messages[processed_count:]
                
                if remaining_messages:
                    with open(self.fallback_file_path, 'w') as f:
                        json.dump(remaining_messages, f, indent=2, default=str)
                else:
                    # Remove empty fallback file
                    self.fallback_file_path.unlink()
                
                self.logger.info(f"Processed {processed_count} fallback messages")
            
        except Exception as e:
            self.logger.error(f"Error processing fallback messages: {str(e)}")
    
    def get_fallback_message_count(self) -> int:
        """
        Get the number of messages in the fallback file.
        
        Returns:
            int: Number of queued fallback messages
        """
        try:
            if self.fallback_file_path.exists():
                with open(self.fallback_file_path, 'r') as f:
                    messages = json.load(f)
                return len(messages)
        except Exception:
            pass
        return 0
    
    def transmit_message(self, message_data: Dict) -> Dict:
        """
        Transmit a message with automatic fallback to file storage.
        
        Args:
            message_data (Dict): Dictionary containing message data
        
        Returns:
            Dict: Dictionary containing the transmitted message with metadata
        """
        try:
            # Validate input
            if not isinstance(message_data, dict):
                raise ValueError("message_data must be a dictionary")
            
            if not message_data:
                raise ValueError("message_data cannot be empty")
            
            # Create a copy of the original data
            composed_message = message_data.copy()
            
            # Add transmission metadata
            composed_message['_timestamp'] = datetime.now().isoformat()
            composed_message['_message_id'] = f"msg_{int(datetime.now().timestamp() * 1000)}"
            composed_message['_total_fields'] = len(message_data)
            
            # Try RabbitMQ first
            success = False
            transmission_method = "fallback_file"
            
            if self.is_connected():
                success = self._publish_to_rabbitmq(composed_message)
                if success:
                    transmission_method = "rabbitmq"
            
            # Fallback to file storage if RabbitMQ failed
            if not success:
                success = self._save_to_fallback_file(composed_message)
                if not success:
                    raise RuntimeError("Both RabbitMQ and fallback file transmission failed")
            
            # Add transmission method to message
            composed_message['_transmission_method'] = transmission_method
            composed_message['_fallback_queue_size'] = self.get_fallback_message_count()
            
            # Log the transmission
            field_summary = []
            for key, value in message_data.items():
                str_value = str(value)
                field_summary.append(f"{key}: '{str_value[:50]}{'...' if len(str_value) > 50 else ''}'")
            
            self.logger.info(f"Message transmitted via {transmission_method} with {len(message_data)} fields")
            self.logger.debug(f"Fields: {', '.join(field_summary[:5])}")
            
            return composed_message
            
        except Exception as e:
            self.logger.error(f"Failed to transmit message: {str(e)}")
            raise
    
    def get_status(self) -> Dict:
        """
        Get current transmitter status.
        
        Returns:
            Dict: Status information
        """
        return {
            "connected": self.is_connected(),
            "rabbitmq_host": self.rabbitmq_host,
            "rabbitmq_port": self.rabbitmq_port,
            "queue_name": self.queue_name,
            "fallback_messages": self.get_fallback_message_count(),
            "fallback_file": str(self.fallback_file_path),
            "use_ssl": self.use_ssl
        }
    
    def close_connection(self):
        """Close the RabbitMQ connection and stop monitoring."""
        self._stop_monitoring = True
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
        
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                self.logger.info("RabbitMQ connection closed")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {str(e)}")
        
        self.connected = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close_connection()


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    def connection_status_callback(connected: bool):
        """Callback function to handle connection status changes"""
        status = "CONNECTED" if connected else "DISCONNECTED"
        print(f"RabbitMQ Status Changed: {status}")
    
    print("Enhanced Message Transmitter with Fallback Demo")
    print("=" * 50)
    
    # Example with callback for status monitoring
    try:
        transmitter = EnhancedMessageTransmitter(
            rabbitmq_host='localhost',
            rabbitmq_port=5672,
            queue_name='test_fallback_queue',
            status_callback=connection_status_callback,
            connection_timeout=2.0,  # Quick timeout for demo
            retry_interval=10.0  # Retry every 10 seconds
        )
        
        # Show initial status
        status = transmitter.get_status()
        print(f"Initial Status: {status}")
        
        # Send some test messages
        for i in range(3):
            message = {
                "test_id": i,
                "message": f"Test message #{i}",
                "timestamp": datetime.now().isoformat(),
                "priority": "normal"
            }
            
            result = transmitter.transmit_message(message)
            print(f"Message {i} sent via: {result.get('_transmission_method')}")
            
            # Wait a bit between messages
            time.sleep(1)
        
        # Show final status
        final_status = transmitter.get_status()
        print(f"Final Status: {final_status}")
        
        if final_status['fallback_messages'] > 0:
            print(f"Note: {final_status['fallback_messages']} messages queued in fallback file")
            print(f"Fallback file location: {final_status['fallback_file']}")
            print("These will be automatically sent when RabbitMQ becomes available")
        
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        if 'transmitter' in locals():
            transmitter.close_connection()
    
    print("\nDemo completed!")
