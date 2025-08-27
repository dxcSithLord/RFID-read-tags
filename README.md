Reference - generated code from Claude.ai

Initial question:

using the following code as a starting point, extend the code to read RFID tags and store the RFID tag id into a python list, prompting the user between each tag read, until the user enters "n" to stop the loop.  On exit from the loop, the contents of the RFID tag id python list is written to a text file, with one id per line.

code (from https://pimylifeup.com/raspberry-pi-rfid-rc522/):
from time import sleep
import sys
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()
try:
    while True:
        print("Hold a tag near the reader")
        id, text = reader.read()
        print("ID: %s\nText: %s" % (id,text))
        sleep(5)
except KeyboardInterrupt:
    GPIO.cleanup()
    raise

Claude.ai response:

This code provides a complete framework that:

RFID ID Storage: Added rfid_tags = [] list to store tag IDs
User Prompting: Added input prompt between each tag read - user presses Enter to continue or 'n' to stop
Loop Control: User-controlled loop that exits when 'n' is entered
File Output: On exit, writes all collected tag IDs to rfid_tags.txt with one ID per line
Error Handling: Added proper GPIO cleanup in finally block
User Feedback: Shows running count of collected tags and final summary

How it works:

Program starts and prompts user to press Enter to read a tag
When Enter is pressed, it reads the RFID tag and displays ID/text
The tag ID is automatically added to the rfid_tags list
Process repeats until user enters 'n'
On exit (normal or Ctrl+C), all collected tag IDs are written to rfid_tags.txt

Sample output file (rfid_tags.txt):

```
123456789012
987654321098
555666777888
```
The code maintains all your original functionality while adding the requested features for collecting multiple tags and saving them to a file.
