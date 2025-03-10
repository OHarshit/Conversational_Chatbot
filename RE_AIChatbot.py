import streamlit as st
import os
from groq import Groq
import random
import traceback

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
    os.environ['GROQ_API_KEY1'] = "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"
    groq_api_key1 = os.environ['GROQ_API_KEY1']
    os.environ['GROQ_API_KEY2'] = "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"
    groq_api_key2 = os.environ['GROQ_API_KEY2']

    # Display the Groq logo
    spacer, col = st.columns([5, 1])
    #with col:
    #   st.image('resources/logo.png')

    # The title and greeting message of the Streamlit application
    st.title("Chat with RE.AI!")
    st.write(
        "Namaste! I'm RE.AI - your smart guide to India's real estate. Whether you're eyeing a stylish Bangalore bungalow or a chic flat in Mumbai, let's chat and find your perfect nest!")

    # Add customization options to the sidebar
    # st.sidebar.title('Customization')
    # system_prompt = st.sidebar.text_input("System prompt:")

    with open("resources/classifier_prompt_corrected.txt", "r", encoding="utf-8") as file:
        classifier_prompt = file.read()

    #with open("resources/prompt.txt", "r", encoding="utf-8") as file:
    with open("resources/prompt.txt","r", encoding="utf-8" ) as file:
        system_prompt = file.read()

    # print(system_prompt)

    # model = st.sidebar.selectbox(
    #     'Choose a model',
    #     ['llama3-8b-8192', 'mixtral-8x7b-32768']
    # )

    # model = 'llama3-8b-8192'
    model = 'llama3-70b-8192'
    model1 = 'deepseek-r1-distill-llama-70b'
    #model = 'qwen-2.5-32b'

    
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
    #while True:
    if submit_button and user_question:
        user_intent_flag = get_user_intent(classifier_prompt,memory,user_question,groq_api_key,groq_api_key1,groq_api_key2,model1)
        print(user_intent_flag)

        token = user_intent_flag.split("</think>")[1]
        print(token)
        if 'MALICIOUS_INPUT' not in token:
            # Construct chat prompt template
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),  # To maintain context
                HumanMessagePromptTemplate.from_template("{human_input}"),
            ])

            response = try_various_keys(groq_api_key, groq_api_key1, groq_api_key2, prompt, model, memory, user_question)
            city_mapping = {'ahmedabad':1, 'chennai':1, 'delhi':1, 'gurgaon':1, 'hyderabad':1, 'kolkata':1, 'noida':1, 'ghaziabad':1, 'pune':1, 'bengaluru':1, 'mumbai':1}


            poly_mapping = pd.read_csv('resources/Top11City_locality_poly_mapping.csv')
            poly_mapping['locality_name'] = poly_mapping['locality_name'].apply(lambda x: x.lower())
            locality_mapping = {locality: locality for locality in poly_mapping['locality_name'].unique()}

            apartment_type_mapping = {'office':54,'residential':54,'1 bhk':2,'2 bhk':3,'3 bhk':4,
                                        'shop':54,'residential plot':54,'3+ bhk':5,'showroom':54,'agricultural land':70,'1 rk':1,
                                        '4 bhk':5,'5 bhk':5,'6 bhk':5,'7 bhk':5,'8 bhk':5}

            furnish_type_mapping = {'semi-furnished':2,'unfurnished':3,'fully furnished':1}

            property_type_mapping = {'shop':39,'independent house':2,'villa':38,'plot':37,'independent floor':35,'apartment':1,'office':40}

            base_url = 'https://recommendation.housing.com/recommended-properties/?query_unique_id=1&page_size=10&uid=123458765544'
            khoj_buy_base_url = "https://khoj.housing.com/api/v9/buy/index/filter?buy_listing30=true"
            khoj_rent_base_url = "https://khoj.housing.com/api/v2/rent/index/filter?rent_listing30=true"

            # &service=buy&type=resale&
            # &city_name=mumbai&poly=e132fcd7870f8379a5e1
            try:
                print(response)
                response = get_JSON(response)
                print(response)
                json_query = json.loads(response)
                url,flag = construct_url(json_query,city_mapping,locality_mapping,furnish_type_mapping,apartment_type_mapping,property_type_mapping,base_url)
                #response = url

                if flag==0:
                    response = "Got a city in mind? Drop it here, and I'll track down your dream home!"
                    raise Exception(response)
                elif flag==1:
                    response = "Oops! Looks like your city’s playing hide and seek. Try dropping another city name, and I’ll fetch the best spots!"

                    raise Exception(response)

                response = requests.get(url,verify=False)

                # Send a GET request
                print(response.text)  # Print the response content
                data = response.json()
                all_flats = data['data']['flat_id_personal_score_pair']
                public_urls = []
                url_rent_base = 'https://housing.com/rent/'
                url_buy_base = 'https://housing.com/in/buy/resale/page/'
                all_flats_khoj = []
                is_buy = False
                for i,val in enumerate(all_flats):
                    print(val)
                    if val['service_type'] == 'resale':
                        is_buy = True
                        public_urls.append(url_buy_base+str(val['flat_id'])+'-'+'property')
                    else:
                        public_urls.append(url_rent_base+str(val['flat_id'])+'-'+'property')
                    all_flats_khoj.append(str(val['flat_id']))
                all_flats_khoj_str=','.join(all_flats_khoj)
                # print(all_flats_khoj_str)
                description_json_str = ''
                if len(all_flats)==0:
                    response = "Oops, seems our property search is playing hide and seek! Maybe loosen those filters a bit or double-check them for any cheeky mix-ups."
                    raise Exception("all_flats equal to zero")
                else:
                    if is_buy:
                        khoj_buy_base_url = khoj_buy_base_url + "&flat_ids=" + all_flats_khoj_str
                        description_json_str = requests.get(khoj_buy_base_url,verify=False)
                    else:
                        khoj_rent_base_url = khoj_rent_base_url + "&flat_ids=" + all_flats_khoj_str
                        description_json_str = requests.get(khoj_rent_base_url,verify=False)
                    # print(khoj_buy_base_url,khoj_rent_base_url)

                    description_json_json = description_json_str.json()

                    description_json_list = description_json_json['data']['hits']

                    #description_json_dict = {value['id']:value['description'] for idx,value in enumerate(description_json_list)  }
                    description_json_dict={}
                    for idx,value in enumerate(description_json_list):
                        if value['description'] is None:
                            description_json_dict[str(value['id'])] =''
                        else:
                            description_json_dict[str(value['id'])] = truncate_scraped_content(value['description'])



                    print(description_json_dict)

                Output_string = ''
                # print(len(public_urls))
                flag_for_url=0
                count=0
                public_urls=public_urls[0:5]
                for i,url in enumerate(public_urls):
                    flat_id = url.split('/')[-1].split('-')[0]
                    if flat_id in description_json_dict.keys():
                        Output_string = Output_string + url + " "
                        Output_string = Output_string + '\n'

                        Output_string = Output_string + " " + description_json_dict.get(
                            flat_id)  # description_json_list[i]['description']
                        Output_string = Output_string + ''
                        # if count==(len(public_urls)-1):
                        #     #Output_string = Output_string + summarize_content(get_scraped_content(url),user_question,memory,groq_api_key)
                        #     Output_string = Output_string + truncate_scraped_content(get_scraped_content(url))
                        # else:
                        #     #Output_string = Output_string + summarize_content_brief2(get_scraped_content(url), user_question, memory,groq_api_key)
                        #     Output_string = Output_string + truncate_scraped_content(get_scraped_content(url))
                        Output_string = Output_string + '\n'

                    print(flat_id)

                    flag_for_url = 1
                    count=count+1
                response = Output_string
                print(flag_for_url)
                if flag_for_url==1:
                    with open("resources/prompt_for_summarizing_properties.txt", "r", encoding="utf-8") as file:
                        prompt_for_summary = file.read()
                    response=summarize_content2(Output_string, user_question,prompt_for_summary,memory,groq_api_key,groq_api_key1,groq_api_key2)
                elif Output_string == '':
                    response = "Oops, seems our property search is playing hide and seek! Maybe loosen those filters a bit or double-check them for any cheeky mix-ups."
                #elif int(flag_for_url)==1:

                print(flag_for_url)
            except Exception as e:
                print(e)
                traceback.print_exc()

        # Save context in memory
        else:
            response = "Nice try! 😏 But I’m here to find you a home, not to break into one! Let’s stick to real estate, shall we? 🚀🏡"
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