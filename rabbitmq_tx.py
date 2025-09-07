import logging
import json
import pika
import os
import ssl
from datetime import datetime
from typing import Dict, Optional
from enhanced_config_manager import EnhancedConfigManager
import time

class MessageTransmitter:
    """
    Updated MessageTransmitter with tx_message.py compatible RabbitMQ publishing
    """
    
    def __init__(self, config: EnhancedConfigManager, status_callback=None, **kwargs):
        """
        Initialize MessageTransmitter with configuration manager
        
        Args:
            config: EnhancedConfigManager instance
            status_callback: Callback for connection status changes
        """
        self.config = config
        self.status_callback = status_callback
        self.rabbitmq_channel = None
        self.rabbitmq_connection = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize RabbitMQ connection
        self._connect_to_rabbitmq()
    
    def _connect_to_rabbitmq(self):
        """Establish RabbitMQ connection"""
        try:
            rabbitmq_config = self.config.rabbitmq
            
            # Create connection parameters
            credentials = None
            if rabbitmq_config.username and rabbitmq_config.password:
                credentials = pika.PlainCredentials(
                    rabbitmq_config.username, 
                    rabbitmq_config.password
                )
            
            parameters = pika.ConnectionParameters(
                host=rabbitmq_config.host,
                port=rabbitmq_config.port,
                virtual_host=rabbitmq_config.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=5.0
            )
            
            self.rabbitmq_connection = pika.BlockingConnection(parameters)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            
            # Declare exchange and queue if needed
            if rabbitmq_config.exchange:
                self.rabbitmq_channel.exchange_declare(
                    exchange=rabbitmq_config.exchange,
                    exchange_type='direct',
                    durable=True
                )
            
            self.rabbitmq_channel.queue_declare(
                queue=rabbitmq_config.queue_name,
                durable=True
            )
            
            self.logger.info(f"Connected to RabbitMQ at {rabbitmq_config.host}:{rabbitmq_config.port}")
            
            if self.status_callback:
                self.status_callback(True)
                
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            self.rabbitmq_channel = None
            self.rabbitmq_connection = None
            
            if self.status_callback:
                self.status_callback(False)
    
    def send_rabbitmq_message(self, message):
        """Send message to RabbitMQ or log locally (same as tx_message.py)"""
        try:
            if self.rabbitmq_channel:
                rabbitmq_config = self.config.rabbitmq
                
                self.rabbitmq_channel.basic_publish(
                    exchange=rabbitmq_config.exchange,
                    routing_key=rabbitmq_config.routing_key_scan,
                    body=json.dumps(message, indent=2),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                        timestamp=int(time.time())
                    )
                )
                
                print(f"📤 RabbitMQ Message Sent Successfully")
                self.logger.info(f"RabbitMQ: {message['object_code']} at {message['location_code']}")
                return True
            else:
                print("📋 LOCAL MODE - Message logged:")
                print(json.dumps(message, indent=2))
                self.logger.info(f"LOCAL: {message['object_code']} at {message['location_code']}")
                return False
                
        except Exception as e:
            print(f"❌ Message sending failed: {e}")
            print("📋 Logging message locally:")
            print(json.dumps(message, indent=2))
            self.logger.error(f"Message send failed: {e}")
            return False

    def transmit_message(self, message_data: Dict) -> Dict:
        """
        Transmit message using send_rabbitmq_message method
        
        Args:
            message_data: Message dictionary to send
            
        Returns:
            The transmitted message
        """
        try:
            # Validate message format
            required_fields = ['object_code', 'location_code', 'timestamp', 'scanner_id']
            for field in required_fields:
                if field not in message_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Send the message
            success = self.send_rabbitmq_message(message_data)
            
            # Add transmission metadata
            message_data['_transmission_success'] = success
            message_data['_transmission_method'] = 'rabbitmq' if success else 'local_log'
            
            return message_data
            
        except Exception as e:
            self.logger.error(f"Failed to transmit message: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if RabbitMQ connection is active"""
        if not self.rabbitmq_connection or self.rabbitmq_connection.is_closed:
            return False
        
        try:
            self.rabbitmq_connection.process_data_events(time_limit=0)
            return True
        except Exception:
            return False

    def cleanup(self):
        """Clean up RabbitMQ connection"""
        try:
            if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
                self.rabbitmq_connection.close()
                self.logger.info("RabbitMQ connection closed")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {e}")


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
