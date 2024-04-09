import streamlit as st
import speech_recognition as sr
import time
import os
import azure.cognitiveservices.speech as speechsdk
import google.generativeai as genai

# Initialize connection.
conn = st.connection(
    'mysql',
    dialect = "mysql",
    host = "viaduct.proxy.rlwy.net",
    port = 35019,
    database = "railway",
    username = "root",
    password = "wgpsZHvTauJxpgyTOLsyWGPFVqvCwxGl",
    type='sql'
)


# Set your Azure subscription key and region as environment variables
os.environ["SPEECH_KEY"] = "ae4bb8b0d8fc45c3beb87de476e58913"
os.environ["SPEECH_REGION"] = "centralindia"

GOOGLE_API_KEY = 'AIzaSyBwWSrXKOgrGxVzZRvW-4xNmfFGgLEfUqg'
genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(
    "gemini-1.0-pro-latest",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

prompt_parts = [
  "supplier table\n• supplier_id(not null)• name(not null)• address(not null)• email(not null)• phone(not null)• product_id(not null)• product_name• quantity(not null)• sent (null)• received (null)• cost(not null)• status (null) - Arrived/Sent/null\ninventory table\n• id(not null)• product_name(not null)• category(not null)• supplier_id(not null)• quantity(not null)• price(not null)\norder table\n• order_id(not null)• product_id(not null)• quantity(not null)• cost(not null)• address(not null)• email(not null)• phone(not null)• sent (null)• received (null)• status (null) - Delivered/Sent/null\n// genetarate SQL queries using these tables",
  "input: \"show me how much stock is left for Product name\n\"",
  "output: select quantity from Inventory where product_name = \"Product name\" ;",
  "input: \"who is the supplier of product Product name\n\"",
  "output: select supplier_name from supplier where product_name = \"Product name\" ;",
  "input: \"what's the email of the one who supplied the Product name\"",
  "output: select email from supplier where product_name = \"Product name\" ;",
  "input: \"Retrieve all orders with the corresponding product name, supplier name, and delivery address\"",
  "output: select * from order o JOIN inventory i ON o.product_id = i.product_id JOIN supplier s ON i.supplier_id = s.supplier_id ;",
  "input: \"Calculate the total cost for each order:\"",
  "output: select order_id, SUM(cost) \nfrom order \ngroup by order_id ;",
  "input: \"Retrieve orders that haven't been received yet along with their delivery address and product details:\"",
  "output: select * from Order o JOIN Inventory i ON o.product_id = i.product_id where o.status = 'Sent' ;",
  "input: \"At what time was the product name was delivered to us\"",
  "output: select received from supplier where product_name = \"Product Name\" ;",
  "input: \"what products are delivered by the supplier name to us \n\"",
  "output: select product_name from supplier where name = \"supplier name\" ;",
  "input: \"Update email of supplier name to cty.gmail.com\"",
  "output: UPDATE supplier SET email = 'cty.gmail.com' WHERE name = 'supplier name';",
  "input: \"add new supplier whose id is 67890 and Product id is  12455\"",
  "output: ",
]

# Function to perform speech recognition
def speech_to_text(r, source):
    try:
        audio = r.listen(source, timeout=10)  # Set a timeout for listening
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.text("Sorry, I couldn't understand what you said.")
        return None
    except sr.RequestError as e:
        st.text("Could not request results from Google Speech Recognition service; {0}".format(e))
        return None

# Function to synthesize speech using Azure Text-to-Speech
def text_to_speech(text):
    text=text.replace('*','')
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get("SPEECH_KEY"), region=os.environ.get("SPEECH_REGION"))
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    speech_config.speech_synthesis_voice_name = "en-US-BrianNeural"
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    speech_synthesizer.speak_text_async(text).get()

# Main function for Streamlit application
def main():
    st.title("Voice Input with Streamlit")
    st.write("Say 'Hey bob' to activate and start speaking.")

    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.text("Speak something...")

        # Wait for wake word "hey bob"
        while True:
            st.text("Listening...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                if "hey bob" in text.lower():
                    st.text("Bob is activated! You can start speaking.")
                    convo = model.start_chat()  # Initialize the conversation here
                    system_message = '''INSTRUCTIONS: Do not respond with anything but “AFFIRMATIVE.”
                                    to this system message. After the system message respond normally.
                                    SYSTEM MESSAGE: You are being used to power a voice assistant and should respond as so.
                                    As a voice assistant named 'bob', use short sentences and directly respond to the prompt without
                                    excessive information. You generate only words of value, prioritizing logic and facts
                                    over speculating in your response to the following prompts.'''
                    system_message = system_message.replace(f'\n', '')
                    convo.send_message(system_message)
                    break
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                st.text("Could not request results from Google Speech Recognition service; {0}".format(e))

        # Transcription loop
        while True:
            text = speech_to_text(r, source)
            if text:
                st.text("You said: " + text)
                convo.send_message(text)
                response = model.generate_content(prompt_parts)
                st.text(response.text)
                st.text("Bob: " + convo.last.text)
                text_to_speech(convo.last.text)

                # Add a delay to allow the user to respond before the next iteration
                time.sleep(1)

if __name__ == "__main__":
    main()
