import streamlit as st
import speech_recognition as sr
import time
import os
import azure.cognitiveservices.speech as speechsdk
import google.generativeai as genai
from langchain_helper import get_few_shot_db_chain
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
# Initialize connection.
conn=mysql.connector.connect(
    host = "viaduct.proxy.rlwy.net",
    user = "root",
    password = "wgpsZHvTauJxpgyTOLsyWGPFVqvCwxGl",
    database = "railway",
    port = 35019
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

# Function to execute database-related queries
def execute_query(text):
    keywords = ["table","change","display","show me", "retrieve", "calculate", "update", "add new","remaining","stocks","orders","order","shirt","insert","entry","add","new","product","get me"]
    for keyword in keywords:
        if keyword in text.lower():
            return True
    return False

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
                    text_to_speech("Bob is activated! You can start speaking.")
                    convo = model.start_chat(history=[
  {
    "role": "user",
    "parts": ["supplier table\n• supplier_id(not null)• name(not null)• address(not null)• email(not null)• phone(not null)• product_id(not null)• product_name• quantity(not null)• sent (null)• received (null)• cost(not null)• status (null) - Arrived/Sent/null\ninventory table\n• id(not null)• product(not null)• category(not null)• supplier_id(not null)• quantity(not null)• price(not null)\norder table\n• order_id(not null)• product_id(not null)• quantity(not null)• cost(not null)• address(not null)• email(not null)• phone(not null)• sent (null)• received (null)• status (null) - Delivered/Sent/null"]
  },
  {
    "role": "model",
    "parts": ["```sql\nSELECT\n  s.supplier_id,\n  s.name AS supplier_name,\n  s.email AS supplier_email,\n  s.phone AS supplier_phone,\n  o.order_id,\n  o.quantity AS order_quantity,\n  o.cost AS order_cost,\n  o.address AS order_address,\n  o.email AS order_email,\n  o.phone"]
  },
  {
    "role": "user",
    "parts": ["Update email of supplier name to cty.gmail.com"]
  },
  {
    "role": "model",
    "parts": ["```sql\nUPDATE supplier\nSET email = 'cty.gmail.com'\nWHERE\n  name = 'Supplier Name';\n```"]
  },
  {
    "role": "user",
    "parts": ["Retrieve orders that haven't been received yet along with their delivery address and product details"]
  },
  {
    "role": "model",
    "parts": ["```sql\nSELECT\n  o.order_id,\n  o.address AS delivery_address,\n  i.product,\n  o.quantity,\n  o.cost\nFROM orders AS o\nJOIN inventory AS i\n  ON o.product_id = i.product_id\nWHERE\n  o.received IS NULL;\n```"]
  },
  {
    "role": "user",
    "parts": ["who is the supplier of product Product name"]
  },
  {
    "role": "model",
    "parts": ["```sql\nSELECT\n  s.supplier_id,\n  s.name AS supplier_name,\n  s.email AS supplier_email,\n  s.phone AS supplier_phone\nFROM supplier AS s\nJOIN inventory AS i\n  ON s.supplier_id = i.supplier_id\nWHERE\n  i.product = 'Product Name';\n```"]
  },
   {
    "role": "user",
    "parts": ["insert into inventory id is equal to 1 product name is equal to puma category is equal to shirt quantity 3 and price is equal to 90"]
  },
  {
    "role": "model",
    "parts": ["```sql\nINSERT INTO inventory (id, product, category, quantity, price)\nVALUES (1, 'Puma', 'Shirt', 3, 90);\n```"]
  },
])  # Initialize the conversation here
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
                if execute_query(text):
                    text_to_speech("Please wait.....")
                    text_to_speech("Fetching Details from the database....")
                    chain = get_few_shot_db_chain()
                    response = chain.invoke({
        "question": text
    })
                    cursor=conn.cursor()
                    cursor.execute(response)
                    if "SELECT" not in response:
                        conn.commit()
                        if "supplier" in response:
                            cursor.execute("SELECT * FROM supplier;")
                            data=cursor.fetchall()
                            df=pd.DataFrame(data,columns=cursor.column_names)
                            st.dataframe(df)
                        if "orders" in response:
                            cursor.execute("SELECT * FROM orders;")
                            data=cursor.fetchall()
                            df=pd.DataFrame(data,columns=cursor.column_names)
                            st.dataframe(df)
                        if "inventory" in response:
                            cursor.execute("SELECT * FROM inventory;")
                            data=cursor.fetchall()
                            df=pd.DataFrame(data,columns=cursor.column_names)
                            st.dataframe(df)
                    else:

                        data=cursor.fetchall()
                        df=pd.DataFrame(data,columns=cursor.column_names)
                        st.dataframe(df) # Display the SQL query
                        df_string = df.to_string()
                        combined_prompt = f"""
                        using the below given information generate the accurate assistants response according to the user's question and the avaialable SQL Result
                        Question: {text}

                        SQL Result:
                        {df_string}

                        Assistant's Response:
                        Only provide the assitant's response , nothing else
                        """

                        convo.send_message(combined_prompt)
                        text_to_speech(convo.last.text)
                        text_to_speech("Is there anything else i can help you with?")
                else:
                    convo.send_message(text)  # Continue the conversation
                

                # Add a delay to allow the user to respond before the next iteration
                time.sleep(1)

if __name__ == "__main__":
    main()
