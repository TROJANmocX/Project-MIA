from mia_assistant import command_parser

def test_parse_command_youtube():
    intent = command_parser.parse_command("open youtube")
    assert intent["action"] == "open_app"
    assert intent["target"].lower() == "youtube"

def test_parse_command_weather():
    intent = command_parser.parse_command("what's the weather?")
    assert intent["action"] == "get_weather"

def test_parse_command_unknown():
    intent = command_parser.parse_command("abracadabra")
    assert intent["action"] == "unknown"
