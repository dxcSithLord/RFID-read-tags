from time import sleep
import sys
import RPi.GPIO as GPIO
from gpiozero import RGBLED
from colorzero import Color
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()
rfid_tags = {}  # Dictionary to store RFID tag IDs and text values
led = RGBLED(12,13,19)

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
        led.color = Color("white")
        id, text = reader.read()
        print("ID: %s\nText: %s" % (id, text))
        
        # Store the RFID tag ID and text in the dictionary (only if unique)
        tag_id_str = str(id)
        if tag_id_str not in rfid_tags:
            rfid_tags[tag_id_str] = text
            print(f"Tag ID {id} added to collection.")
            led.color = Color("green")
        else:
            print(f"Tag ID {id} already exists in collection - skipping duplicate.")
            led.color = Color("yellow")
        print(f"Total unique tags collected: {len(rfid_tags)}")

    led.color = Color("lightblue")
except KeyboardInterrupt:
    print("\nProgram interrupted by user.")
finally:
    GPIO.cleanup()
    
    # Write RFID tag IDs and text to file on exit
    if rfid_tags:
        filename = "rfid_tags.txt"
        try:
            with open(filename, 'w') as file:
                for tag_id, tag_text in rfid_tags.items():
                    file.write(f"{tag_id}: {tag_text}\n")
            
            print(f"\nSuccessfully saved {len(rfid_tags)} RFID tag IDs to '{filename}'")
            print("Saved tag data:")
            for i, (tag_id, tag_text) in enumerate(rfid_tags.items(), 1):
                print(f"  {i}: {tag_id} - {tag_text}")
                
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("No RFID tags were collected.")
