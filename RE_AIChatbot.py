import streamlit as st
import os
from groq import Groq
import random

from langchain.chains import ConversationChain, LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory, ConversationBufferMemory
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import json
import requests

from src.utils import *


def main():
    """
    This function is the main entry point of the application. It sets up the Groq client, the Streamlit interface, and handles the chat interaction.
    """

    # Get Groq API key
    os.environ['GROQ_API_KEY'] = "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"
    groq_api_key = os.environ['GROQ_API_KEY']

    # Display the Groq logo
    spacer, col = st.columns([5, 1])
    with col:
        st.image('resources/logo.png')

    # The title and greeting message of the Streamlit application
    st.title("Chat with RE.AI!")
    st.write(
        "Namaste! I'm RE.AI - your smart guide to India's real estate. Whether you're eyeing a stylish Bangalore bungalow or a chic flat in Mumbai, let's chat and find your perfect nest!")

    # Add customization options to the sidebar
    # st.sidebar.title('Customization')
    # system_prompt = st.sidebar.text_input("System prompt:")

    with open("resources/prompt.txt", "r", encoding="utf-8") as file:
        system_prompt = file.read()
    # print(system_prompt)

    # model = st.sidebar.selectbox(
    #     'Choose a model',
    #     ['llama3-8b-8192', 'mixtral-8x7b-32768']
    # )

    # model = 'llama3-8b-8192'
    # model = 'llama3-70b-8192'
    # model = 'deepseek-r1-distill-llama-70b'
    model = 'qwen-2.5-32b'

    
    # conversational_memory_length = st.sidebar.slider('Conversational memory length:', 1, 10, value=5)
    conversational_memory_length = 10

    memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history", return_messages=True)
    #memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        memory.save_context({"input": message["content"]}, {"output": ""})

    # Display chat history on Streamlit UI
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):  # Use 'user' and 'assistant'
                st.write(message["content"])

    # User input
    # ✅ Reset input BEFORE the widget is created
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    # ✅ Use a form to handle input submission
    with st.form(key="chat_form"):
        user_question = st.text_area("Ask a question:", value=st.session_state.user_input, key="user_input")
        submit_button = st.form_submit_button("Send")
    #user_question = st.text_input("Ask a question:")

    # Initialize Groq Langchain chat object
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model)
    #while True:
    if submit_button and user_question:
        # Construct chat prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),  # To maintain context
            HumanMessagePromptTemplate.from_template("{human_input}"),
        ])

        # Create conversation chain
        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=True,
            memory=memory,
        )



        # Get chatbot response
        response = conversation.predict(human_input=user_question)

        city_mapping = {'ahmedabad':1, 'chennai':1, 'delhi':1, 'gurgaon':1, 'hyderabad':1, 'kolkata':1, 'noida':1, 'ghaziabad':1, 'pune':1, 'bengaluru':1, 'mumbai':1}


        poly_mapping = pd.read_csv('resources/Top11City_locality_poly_mapping.csv')
        poly_mapping['locality_name'] = poly_mapping['locality_name'].apply(lambda x: x.lower())
        locality_mapping = {locality: locality for locality in poly_mapping['locality_name'].unique()}

        apartment_type_mapping = {'office':54,'residential':54,'1 bhk':2,'2 bhk':3,'3 bhk':4,
                                    'shop':54,'residential plot':54,'3+ bhk':5,'showroom':54,'agricultural land':70,'1 rk':1}

        furnish_type_mapping = {'semi-furnished':2,'unfurnished':3,'fully furnished':1}

        property_type_mapping = {'shop':39,'independent house':2,'villa':38,'plot':37,'independent floor':35,'apartment':1,'office':40}

        base_url = 'https://recommendation.housing.com/recommended-properties/?query_unique_id=1&page_size=10&uid=123458765544'
        # &service=buy&type=resale&
        # &city_name=mumbai&poly=e132fcd7870f8379a5e1
        try:
            response = get_JSON(response)
            json_query = json.loads(response)
            url = construct_url(json_query,city_mapping,locality_mapping,furnish_type_mapping,apartment_type_mapping,property_type_mapping,base_url)
            response = url
            
            response = requests.get(url,verify=False)  # Send a GET request
            print(response.text)  # Print the response content
            data = response.json()
            all_flats = data['data']['flat_id_personal_score_pair']
            public_urls = []
            url_rent_base = 'https://housing.com/rent/'
            url_buy_base = 'https://housing.com/in/buy/resale/page/'
            for i,val in enumerate(all_flats):
                if val['service_type'] == 'resale':
                    public_urls.append(url_buy_base+str(val['flat_id'])+'-')
                else:
                    public_urls.append(url_rent_base+str(val['flat_id'])+'-')

            Output_string = ''
            print(len(public_urls))
            for url in public_urls:
                Output_string = Output_string + url
                Output_string = Output_string + '\n'
            response = Output_string

            if Output_string == '':
                response = "Oops, seems our property search is playing hide and seek! Maybe loosen those filters a bit or double-check them for any cheeky mix-ups."

        except Exception as e:
            print(e)

        # Save context in memory
        memory.save_context({"input": user_question}, {"output": response})

        # Store the conversation in session state
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
        #st.write("Chatbot:", response)
        #st.session_state.user_input = ""  # Reset input field
        st.session_state.pop("user_input", None)
        st.experimental_rerun()
        #st.session_state.user_input = ""

if __name__ == "__main__":
    # url = "https://recommendation.housing.com/recommended-properties/?query_unique_id=1&page_size=10&uid=123458765544&city_name=gurgaon&min_price=1&service=buy&type=resale"  # Replace with your actual URL
    
    main()