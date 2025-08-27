from time import sleep
import sys
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()
rfid_tags = []  # List to store RFID tag IDs

try:
    print("RFID Tag Collection")
    print("===================")
    print("Follow the prompts to read tags. Enter 'n' when finished.")
    
    while True:
        # Prompt user between each tag read
        user_input = input("\nPress Enter to read a tag (or 'n' to stop): ").strip().lower()
        
        if user_input == 'n':
            print("Stopping tag collection...")
            break
        
        print("Hold a tag near the reader")
        id, text = reader.read()
        print("ID: %s\nText: %s" % (id, text))
        
# Store the RFID tag ID in the list (only if unique)
        tag_id_str = str(id)
        if tag_id_str not in rfid_tags:
            rfid_tags.append(tag_id_str)
            print(f"Tag ID {id} added to collection.")
        else:
            print(f"Tag ID {id} already exists in collection - skipping duplicate.")
        print(f"Total unique tags collected: {len(rfid_tags)}")
        
        
except KeyboardInterrupt:
    print("\nProgram interrupted by user.")
finally:
    GPIO.cleanup()
    
    # Write RFID tag IDs to text file on exit
    if rfid_tags:
        filename = "rfid_tags.txt"
        try:
            with open(filename, 'w') as file:
                for tag_id in rfid_tags:
                    file.write(f"{tag_id}\n")
            
            print(f"\nSuccessfully saved {len(rfid_tags)} RFID tag IDs to '{filename}'")
            print("Saved tag IDs:")
            for i, tag_id in enumerate(rfid_tags, 1):
                print(f"  {i}: {tag_id}")
                
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("No RFID tags were collected.")
