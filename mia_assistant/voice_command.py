# mia_assistant/voice_command.py

from mia_assistant import voice_activation

def start_voice_loop():
    while True:
        command = voice_activation.listen_for_command()
        if command:
            voice_activation.execute_command(command)

if __name__ == "__main__":
    start_voice_loop()
