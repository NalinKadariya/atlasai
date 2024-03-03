from pathlib import Path
from openai import OpenAI
client = OpenAI(api_key="sk-ssss")
import warnings


'''
speech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input="म डेनिस बोल्छु। तिम्रो नाम के हो?"
)

response.stream_to_file(speech_file_path)
warnings.filterwarnings("ignore",category=DeprecationWarning)
'''
'''
import whisper

model = whisper.load_model("base")
result = model.transcribe("speech.mp3")
print(result["text"])

import requests
host = 'localhost'
port = 5000

response = requests.post(f'http://{host}:{port}/signup', json={'username': "Hi", 'password': "Byedfgrytge", 'gmail': "Hi", 'openai_key': "Byedfgrytge"})
print(response.json())
'''