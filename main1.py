import streamlit as st
import speech_recognition as sr
import time
import os
import azure.cognitiveservices.speech as speechsdk
import google.generativeai as genai
from langchain_helper import get_few_shot_db_chain
from dotenv import load_dotenv
load_dotenv()
# Initialize connection.
conn = st.connection(
    'mysql',
    dialect="mysql",
    host="viaduct.proxy.rlwy.net",
    port=35019,
    database="railway",
    username="root",
    password="wgpsZHvTauJxpgyTOLsyWGPFVqvCwxGl",
    type='sql'
)

# Set your Azure subscription key and region as environment variables
os.environ["SPEECH_KEY"] = "ae4bb8b0d8fc45c3beb87de476e58913"
os.environ["SPEECH_REGION"] = "centralindia"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
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
prompt_parts = ['''You are an expert in converting English questions to SQL code! 
                The SQL database has the name fashion_products 
                and has the following columns - user_id, product_id, product_name, brand, category, price, color, 
                and size.\n\nFor example,\nExample 1 - How many entries of Adidas are present?, 
                the SQL command will be something like this\n``` SELECT COUNT(*) 
                FROM fashion_products WHERE brand = 'Adidas';\n```\n\nExample 2 - 
                How many XL products of Nike are there that have a rating of more than 4
                ?\n```\nSELECT COUNT(*) FROM fashion_products WHERE brand = 'Nike' AND size = 'XL' AND 
                \"Rating\" > 4;\n```\n\nExample 3 - \n```\nSELECT product_name FROM fashion_products 
                WHERE price = (SELECT MAX(price) FROM fashion_products);\n```\n\nDont include ``` and \n in the output''']
prompt_parts = [
    "supplier table\n• supplier_id(not null)• name(not null)• address(not null)• email(not null)• phone(not null)• product_id(not null)• product_name• quantity(not null)• sent (null)• received (null)• cost(not null)• status (null) - Arrived/Sent/null\ninventory table\n• id(not null)• product_name(not null)• category(not null)• supplier_id(not null)• quantity(not null)• price(not null)\norder table\n• order_id(not null)• product_id(not null)• quantity(not null)• cost(not null)• address(not null)• email(not null)• phone(not null)• sent (null)• received (null)• status (null) - Delivered/Sent/null\n// genetarate SQL queries using these tables",
    "input: \"show me how much stock is left for Product name\n\"",
    "output: select quantity from Inventory where product_name = \"Product name\" ;",
    "input: \"who is the supplier of product Product name\n\"",
    "output: select supplier_name from supplier where product_name = \"Product name\" ;",
    "input: \"what's the email of the one who supplied the Product name\"",
    "output: select email from supplier where product_name = \"Product name\" ;",
    "input: \"Retrieve all orders with the corresponding product name, supplier name, and delivery address\"",
    "output: select * from orders o JOIN inventory i ON o.product_id = i.product_id JOIN supplier s ON i.supplier_id = s.supplier_id ;",
    "input: \"Calculate the total cost for each order:\"",
    "output: select order_id, SUM(cost) \nfrom order \ngroup by order_id ;",
    "input: \"Retrieve orders that haven't been received yet along with their delivery address and product details:\"",
    "output: select * from orders o JOIN Inventory i ON o.product_id = i.product_id where o.status = 'Sent' ;",
    "input: \"At what time was the product name was delivered to us\"",
    "output: select received from supplier where product_name = \"Product Name\" ;",
    "input: \"what products are delivered by the supplier name to us \n\"",
    "output: select product_name from supplier where name = \"supplier name\" ;",
    "input: \"Update email of supplier name to cty.gmail.com\"",
    "output: UPDATE supplier SET email = 'cty.gmail.com' WHERE name = 'supplier name';",
    "input: \"add new supplier whose id is 67890 and Product id is  12455\"",
    "output: INSERT INTO supplier (supplier_id, name, address, email, phone, product_id, product_name, quantity, sent, received, cost, status) VALUES (67890, 'New Supplier', 'New Address', 'new.supplier@email.com', '0123456789', 12455, 'New Product', 10, NULL, NULL, 100, NULL);",
    "input: \"delete supplier with id 12345\"",
    "output: DELETE FROM supplier WHERE supplier_id = 12345 ;",
    # Add more variations as needed
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

# Function to execute database-related queries
def execute_query(text):
    keywords = ["table","change","display","show me", "retrieve", "calculate", "update", "add new","remaining","stocks","orders","order","shirt","insert","entry","add","new","product"]
    for keyword in keywords:
        if keyword in text.lower():
            return True
    return False

# Main function for Streamlit application
def main():
    st.title("Voice Input with Streamlit")
    st.write("Say 'Hey bob' to activate and start speaking.")
    chain = get_few_shot_db_chain()

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
                convo.send_message(text)
                if execute_query(text):
                    db_schema = """

You are an expert in converting English questions to SQL code! The SQL database has the following tables:
1. inventory with columns:
   - id SERIAL PRIMARY KEY NOT NULL,
   - product VARCHAR(255) NOT NULL,
   - category VARCHAR(255) NOT NULL,
   - quantity INT NOT NULL,
   - supplier_id INT NOT NULL,
   - price INT NOT NULL
2. supplier with columns:
   - name VARCHAR(255) NOT NULL,
   - address VARCHAR(255) NOT NULL,
   - email VARCHAR(255) NOT NULL,
   - phone INT NOT NULL,
   - product_id INT NOT NULL,
   - product_name VARCHAR(255) NOT NULL,
   - quantity INT NOT NULL,
   - sent DATE,
   - received DATE,
   - cost INT NOT NULL,
   - status VARCHAR(20),
   - supplier_id INT NOT NULL
3. orders with columns:
   - product_id INT NOT NULL,
   - quantity INT NOT NULL,
   - cost INT NOT NULL,
   - address VARCHAR(255) NOT NULL,
   - email VARCHAR(255) NOT NULL,
   - phone INT NOT NULL,
   - sent DATE,
   - received DATE,
   - status VARCHAR(20),
   - order_id INT NOT NULL

Here are some examples for you to learn from:

Example 1 - Show me how much stock is left for 'Product name'?
SQL query: "SELECT quantity FROM inventory WHERE product_name = 'Product name'"

Example 2 - Who is the supplier of product 'Product name'?
SQL query: "SELECT name FROM supplier WHERE product_name = 'Product name'"

Example 3 - What's the email of the one who supplied the 'Product name'?
SQL query: "SELECT email FROM supplier WHERE product_name = 'Product name'"

Example 4 - Retrieve all orders with the corresponding product name, supplier name, and delivery address.
SQL query: "SELECT * FROM orders o JOIN inventory i ON o.product_id = i.product_id JOIN supplier s ON i.supplier_id = s.supplier_id"

Example 5 - Calculate the total cost for each order.
SQL query: "SELECT order_id, SUM(cost) FROM orders GROUP BY order_id"

Example 6 - Retrieve orders that haven't been received yet along with their delivery address and product details.
SQL query: "SELECT * FROM orders o JOIN inventory i ON o.product_id = i.product_id WHERE o.status = 'Sent'"

Example 7 - At what time was the 'Product name' delivered to us?
SQL query: "SELECT received FROM supplier WHERE product_name = 'Product Name'"

Example 8 - What products are delivered by the 'supplier name' to us?
SQL query: "SELECT product_name FROM supplier WHERE name = 'Supplier name'"

Example 9 - Update email of 'supplier name' to 'cty.gmail.com'
SQL query: "UPDATE supplier SET email = 'cty.gmail.com' WHERE name = 'Supplier name'"

Example 10 - Add new supplier whose id is 67890 and Product id is 12455.
SQL query: "INSERT INTO supplier (supplier_id, name, address, email, phone, product_id, product_name, quantity, sent, received, cost, status) VALUES (67890, 'New Supplier', 'New Address', 'new.supplier@email.com', '0123456789', 12455, 'New Product', 10, NULL, NULL, 100, NULL)"

Example 11 - Delete supplier with id 12345.
SQL query: "DELETE FROM supplier WHERE supplier_id = 12345"
"""
                    convo.send_message(db_schema)
                    convo.send_message(f"generate my sql query for{text}")
                    #convo.send_message(f'convert {convo.last.text} into normal sql text query so that it can be direclty used to retrieve info from the database ')
                    #response = model.generate_content(prompt_parts)
                    st.write(convo.last.text)  # Display the SQL query
                    try:
                        query=convo.last.text.replace('\n',' ')
                        query=query.replace("```",'')
                        query=query.replace("sql",'')
                        df = conn.query(query)  # Execute the SQL query
                        if df is not None:
                            st.write(df)
                        else:
                            st.write("Update successful!")
                    except Exception as e:
                        st.write(e)  # Display any error that occurred
                else:
                    convo.send_message(text)  # Continue the conversation
                st.text("Bob: " + convo.last.text)
                text_to_speech(convo.last.text)

                # Add a delay to allow the user to respond before the next iteration
                time.sleep(1)

if __name__ == "__main__":
    main()
