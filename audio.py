import azure.cognitiveservices.speech as speechsdk

def from_mic():
    audio_config=speechsdk.AudioConfig(use_default_microphone=True)
    speech_config = speechsdk.SpeechConfig(subscription="ae4bb8b0d8fc45c3beb87de476e58913", region="centralindia")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config,audio_config=audio_config)
    while True:
        print("Speak into your microphone.")
        result = speech_recognizer.recognize_once_async().get()
        print(result.text)

from_mic()
