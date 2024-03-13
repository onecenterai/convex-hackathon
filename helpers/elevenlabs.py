from elevenlabs import generate
import os

voice = "Bella"

key = os.environ.get('ELEVENLABS_API_KEY')

def vocalize(text: str):
    try:
        return generate(text, key, voice=voice)
    except Exception as e:
        print(e)