from rapidfuzz import process
import pandas as pd
import re
import json
from langchain.chains import ConversationChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory, ConversationBufferMemory
from langchain_groq import ChatGroq
import requests
from bs4 import BeautifulSoup

def find_best_match(candidate: str, string_dict: dict):
    """
    Finds the best matching key from the dictionary for the given candidate string.

    Args:
        candidate (str): The string to search for.
        string_dict (dict): A dictionary where keys are searchable strings and values are mapped IDs.

    Returns:
        tuple: (best_matching_key, score) where best_matching_key is the key with the highest similarity score.
    """
    if not string_dict:
        return None, 0  # Return None if dictionary is empty

    best_match, score, _ = process.extractOne(candidate, string_dict.keys())

    if score >= 60:
        return best_match, score
    else:
        return None, 0  # No good match found

    return best_match,score

def extract_mapped_ids(input_string,feature_mapped):
    if input_string=='':
        return None
    res_list = []
    if ',' in input_string:
        for i in input_string.split(','):
            best_match,bhk_score = find_best_match(i, feature_mapped)
            if best_match:
                res_list.append(feature_mapped.get(best_match))
        return ",".join(map(str, res_list))
    else:
        best_match,bhk_score = find_best_match(input_string, feature_mapped)
        return feature_mapped.get(best_match)


def construct_url(json_query,city_mapping,locality_mapping,furnish_type_mapping,apartment_type_mapping,property_type_mapping,base_url):
    print(json_query)
    city = json_query['city'].lower()
    locality = json_query['locality'].lower()
    service = json_query['service']
    BHK = json_query['BHK']
    min_price = json_query['min_price']
    max_price = json_query['max_price']
    property_type = json_query['property_type']
    min_area = json_query['min_area']
    max_area = json_query['max_area']
    furnished_type = json_query['furnished_type']

    city_name,city_score = find_best_match(city,city_mapping)

    locality_name = extract_mapped_ids(locality, locality_mapping)

    furnish_type_ids = extract_mapped_ids(furnished_type,furnish_type_mapping)

    apartment_type_ids = extract_mapped_ids(BHK,apartment_type_mapping)

    property_type_ids = extract_mapped_ids(property_type,property_type_mapping)

    print(city_name,furnish_type_ids, apartment_type_ids, property_type_ids)

    print(base_url)

    if city_name:
        base_url = base_url+'&city_name={}'.format(city_name)

    poly_mapping = pd.read_csv('resources/Top11City_locality_poly_mapping.csv')
    poly_mapping['city_name'] = poly_mapping['city_name'].apply(lambda x:x.lower())
    poly_mapping['locality_name'] = poly_mapping['locality_name'].apply(lambda x: x.lower())
    poly_ids =""
    
    if city_name and locality_name:
        res_list =locality_name.split(',')
        print(res_list)
        print(city_name,locality_name)

        if len(res_list)==1:
            poly = poly_mapping.loc[
                (poly_mapping['city_name'] == city_name) & (poly_mapping['locality_name'] == locality_name.lower()),
                'uuid']
            print(poly)
            if len(poly) > 0:
                poly_ids = poly.iloc[0]


        else:
            temp_list=[]
            for locality in res_list:
                poly = poly_mapping.loc[
                    (poly_mapping['city_name'] == city_name) & (poly_mapping['locality_name'] == locality.lower()),
                    'uuid']
                if len(poly)>0:
                    temp_list.append(poly.iloc[0])
            poly_ids=",".join(temp_list)



    elif locality_name:
        res_list = locality_name.split(',')
        if len(res_list) == 1:
            poly = poly_mapping.loc[
                 (poly_mapping['locality_name'] == locality_name.lower()),
                'uuid']
            if len(poly) > 0:
                poly_ids = poly.iloc[0]

        else:
            temp_list = []
            for locality in res_list:
                poly = poly_mapping.loc[
                    (poly_mapping['locality_name'] == locality.lower()),
                    'uuid']
                if len(poly) > 0:
                    temp_list.append(poly.iloc[0])
            poly_ids = ",".join(temp_list)

    if poly_ids!="":
        base_url =base_url +'&poly={}'.format(poly_ids)



    if furnish_type_ids:
        base_url = base_url + '&furnish_type_id={}'.format(furnish_type_ids)
    if apartment_type_ids:
        base_url = base_url + '&apartment_type_id={}'.format(apartment_type_ids)
    if property_type_ids:
        base_url = base_url + '&property_type_id={}'.format(property_type_ids)

    if max_price!='':
        base_url = base_url + '&max_price={}'.format(int(max_price))
    if min_price!='':
        if max_price:
            if int(min_price)==int(max_price):
                min_price = '0'
        base_url = base_url + '&min_price={}'.format(int(min_price)+1)
    
    if max_area!='':
        base_url = base_url + '&max_area={}'.format(int(max_area))
    if min_area!='':
        if max_area:
            if int(min_area)==int(max_area):
                min_area = '0'
        base_url = base_url + '&min_area={}'.format(int(min_area)+1)
    
    if service!='':
        if service == 'rent':
            base_url = base_url + '&service=rent'
            base_url = base_url + '&type=rent'
        else:
            base_url = base_url + '&service=buy'
            base_url = base_url + '&type=resale'
            
    else:
        base_url = base_url + '&service=buy'
        base_url = base_url + '&type=resale'




    print('\n')
    print(base_url)
    flag_for_city = 2
    if city=='':
        flag_for_city=0
    elif city_name==None or city_name=='':
        flag_for_city =1



    return base_url, flag_for_city

    
def get_JSON(text):
    # Match a JSON block using regex (handles nested structures)
    json_match = re.search(r"\{.*\}", text, re.DOTALL)

    if json_match:
        try:
            #extracted_json = json.loads(json_match.group())  # Convert to dict
            return json_match.group()  # ✅ Return extracted JSON
        except json.JSONDecodeError:
            return text

    return text

def summarize_links(output_string, user_question,memory,prompt,groq_api_key):
    #model = 'qwen-2.5-32b'
    model = 'llama3-70b-8192'
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model)
    prompt_template = PromptTemplate(
        input_variables=["output_string", "user_question"],
        template=(
            #f"{prompt}\n\n"
            #f"U have to read the links provided in {output_string} and provide a concise summary of all properties"
            #f'''Check the links given as answer in {output_string} to the user query {user_question} and add reasons why each of the suggested property is correct as per the query.Provide reasons which are non-obvious and unique to each suggestion.Also add what additional parameters that we should ask the user to further refine his search for the parameters.Put this in normal conversational tone.

            #Your response should have all the links provided, reasons against each link & asking the user additional information to improve this response.Response should not be more than 15 lines
            #Please write the reasons against each link under appropriate headers making it readable for the user.'''

            # f'''Fetch information from the links provided in {output_string} as a response to the user query {user_question}. For each suggested property, explain why it is a good match for the query, highlighting non-obvious and unique reasons specific to each listing. Additionally, suggest further parameters that we should ask the user to refine their search. Maintain a conversational and engaging tone.
            # Your response should include:
            # Top 5 property links
            # Reasons for each property, categorized under relevant headers (e.g., Size, Furnishing, Rent,Furnishing,Security Deposit,Floor,Bathrooms,Balconies,Parking,Availability,Property Age,Facing,Project Highlights: etc.)
            # A short section suggesting additional details to improve future recommendations
            # The response should be concise (within 15 lines), easy to read, and user-friendly. Please don't mention user's query in your response. Talk like you are directly responding to {user_question}.Maintain a conversational tone including some suitable emojis.
            # Strictly stick to only the information fetched from the links and don't provide any misinformation.'''

            f'''Summarize the information provided against each of the links'''



        )
    )
    conversation = LLMChain(
        llm=groq_chat,
        prompt=prompt_template,
        verbose=True,
        memory=memory,
    )
    #response = conversation.predict(output_string=output_string, user_question=user_question)
    response = conversation.predict(human_input=output_string)

    return response

def summarize_content(output_string, user_question,memory,groq_api_key):
    model = 'llama3-70b-8192'
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model)
    prompt_template = PromptTemplate(
        input_variables=["output_string", "user_question"],
        template=(
            f'''Summarize the information against the links provided in {output_string} as a response to the user query {user_question}. For each suggested property, explain why it is a good match for the query, highlighting non-obvious and unique reasons specific to each listing. Additionally, suggest further parameters that we should ask the user to refine their search. Maintain a conversational and engaging tone.
             Your response should include:
             Reasons for each property, categorized under relevant headers (e.g., Size, Furnishing, Rent,Furnishing,Security Deposit,Floor,Bathrooms,Balconies,Parking,Availability,Property Age,Facing,Project Highlights: etc.)
             A short section suggesting additional details to improve future recommendations
             The response should be brief and to the point(in bullets), easy to read, and user-friendly. Please don't mention user's query in your response. Talk like you are directly responding to {user_question}.Maintain a conversational tone including some suitable emojis.
             Strictly stick to only the information provided against the links and don't provide any misinformation'''
        )
    )
    conversation = LLMChain(
        llm=groq_chat,
        prompt=prompt_template,
        verbose=True,
        memory=memory,
    )
    # response = conversation.predict(output_string=output_string, user_question=user_question)
    response = conversation.predict(human_input=output_string)

    return response

def summarize_content_brief(output_string, user_question,memory,groq_api_key):
    model = 'llama3-70b-8192'
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model)
    prompt_template = PromptTemplate(
        input_variables=["output_string", "user_question"],
        template=(
            f'''Summarize the information against the links provided in {output_string} as a response to the user query {user_question}. For each suggested property, explain why it is a good match for the query, highlighting non-obvious and unique reasons specific to each listing. Maintain a conversational and engaging tone.
             Your response should include:
             Reasons for each property, categorized under relevant headers (e.g., Size, Furnishing, Rent,Furnishing,Security Deposit,Floor,Bathrooms,Balconies,Parking,Availability,Property Age,Facing,Project Highlights: etc.)
             The response should be brief and to the point(in bullets), easy to read, and user-friendly. Please don't mention user's query in your response. Talk like you are directly responding to {user_question}.Maintain a conversational tone including some suitable emojis.
             Strictly stick to only the information provided against the links and don't provide any misinformation. Please limit ur response to 20 words and remember this is not the end of the chat'''
        )
    )
    conversation = LLMChain(
        llm=groq_chat,
        prompt=prompt_template,
        verbose=True,
        memory=memory,
    )
    # response = conversation.predict(output_string=output_string, user_question=user_question)
    response = conversation.predict(human_input=output_string)

    return response

def summarize_content_brief2(output_string, user_question,memory,groq_api_key):
    model = 'llama3-70b-8192'
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model)
    prompt_template = PromptTemplate(
        input_variables=["output_string", "user_question"],
        template=(
            f'''Summarize the information against the links provided in {output_string} as a response to the user query {user_question} in just 20 words'''
        )
    )
    conversation = LLMChain(
        llm=groq_chat,
        prompt=prompt_template,
        verbose=False,
        memory=memory,
    )
    # response = conversation.predict(output_string=output_string, user_question=user_question)
    response = conversation.predict(human_input=output_string)

    return response

def summarize_content2(output_string, user_question,prompt_for_summary,memory,groq_api_key,groq_api_key1,groq_api_key2):
    #model = 'llama3-70b-8192'
    model = 'llama3-8b-8192'
    prompt_template = PromptTemplate(
        input_variables=["output_string", "user_question"],
        template=(
        #     f'''Summarize the information against the links provided in {output_string} under 20 words or so for each link.
        #      Every link and it's summary should have their own separate bullet points.
        #      Strictly stick to only the information provided against the links and don't provide any misinformation.
        #     Keep the links as it is before the description and do not mention that u are providing any summary. Maintain a conversational and engaging tone.'''

            # f'''Summarize the information against the links provided in {output_string} under 20 words or so for each link.
            #     Your response should include:
            #     Every link and it's summary with their own separate bullet points.
            #     A short section asking the user to provide additional details and relevant questions to improve future recommendations at the end of your response, limit this section to 20 words only.
            #     Strictly stick to only the information provided against the links and don't provide any misinformation.
            #     You do no need to mention that you are providing some summary or additional section. Talk like you are directly responding to user query.
            #    Keep the links as it is before the description and do not mention that u are providing any summary. Maintain a conversational and engaging tone.
            #  You do not need to say that you are providing some summaries at the beginning of your response. Just start responding in a engaging and conversational tone.'''
            #

            f'''Format your response as follows:

Each provided link should be listed first, followed by a concise, engaging, and factual summary (about 20 words per link) of the information present against each link in {output_string}.
At the end, include a brief section (within 20 words) asking for additional details to refine future recommendations.
Only use the information available for each link—avoid assumptions or misinformation.
Maintain a natural, conversational tone without explicitly stating that you are summarizing or requesting more details.
Do not use the phrase -"here are the summaries"; simply present the links with their respective descriptions in a seamless, user-friendly manner.
Ensure the response is engaging, direct, and informative. Refer below example for your reference-''' + f'''{prompt_for_summary}'''
         )
    )
    response = try_various_keys(groq_api_key, groq_api_key1, groq_api_key2, prompt_template, model, memory, user_question)

    return response

def summarize_content3(output_string, user_question,prompt_for_summary,memory,groq_api_key):
    model = 'llama3-70b-8192'
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model, temperature=0.1, top_p=0.9)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=prompt_for_summary),
        MessagesPlaceholder(variable_name="chat_history"),  # To maintain context
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ])
    conversation = LLMChain(
        llm=groq_chat,
        prompt=prompt,
        verbose=False,
        memory=memory,
    )

    response = conversation.predict(human_input=output_string)

    return response


def get_scraped_content(url):
    # Headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    # Fetch the webpage
    response = requests.get(url, headers=headers,verify=False)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse HTML content
        #soup = BeautifulSoup(response.text, "html.parser")
        soup = BeautifulSoup(response.text, "lxml")
        # Find the "About this property" section by text
        about_header = soup.find("div", text="About this property")

        if about_header:
            # The actual content is likely in the next div or sibling
            about_section = about_header.find_next_sibling("div")
            if about_section:
                print("About this Property:")
                content = about_section.get_text(strip=True)
                # print(content)
                return content
            else:
                print("Could not find the property details after the header.")
        else:
            print("Could not find the 'About this Property' section. The page may use JavaScript to load content.")

    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")

def truncate_scraped_content(content):
    temp=content.split('More About This Property')
    temp = temp[0].split('Project Highlights')
    return temp[0]

def get_user_intent(classifier_prompt,memory,user_question,groq_api_key,groq_api_key1,groq_api_key2,model):
    prompt = ChatPromptTemplate.from_messages([
         SystemMessage(content=classifier_prompt),
         #MessagesPlaceholder(variable_name="chat_history"),  # To maintain context
         HumanMessagePromptTemplate.from_template("{human_input}"),
     ])
    response=try_various_keys(groq_api_key,groq_api_key1,groq_api_key2,prompt,model,memory,user_question)
    return response

def try_various_keys(groq_api_key,groq_api_key1,groq_api_key2,prompt,model,memory,user_question):
    groq_chat = ChatGroq(groq_api_key=groq_api_key, model=model, temperature=0.1, top_p=0.9)
    groq_chat1 = ChatGroq(groq_api_key=groq_api_key1, model=model, temperature=0.1, top_p=0.9)
    groq_chat2 = ChatGroq(groq_api_key=groq_api_key2, model=model, temperature=0.1, top_p=0.9)
    try:
        conversation = LLMChain(
            llm=groq_chat,
            prompt=prompt,
            verbose=False,
            memory=memory,
        )
        response = conversation.predict(human_input=user_question)
    except Exception as e:
        print(e)
        try:
            if ("RateLimitError" in str(e)) or ("Rate limit" in str(e)) or ("rate_limit_exceeded" in str(e)):
                conversation = LLMChain(
                    llm=groq_chat1,
                    prompt=prompt,
                    verbose=False,
                    memory=memory,
                )
                response = conversation.predict(human_input=user_question)
        except Exception as e:
            print(e)
            if ("RateLimitError" in str(e)) or ("Rate limit" in str(e)) or ("rate_limit_exceeded" in str(e)):
                conversation = LLMChain(
                    llm=groq_chat2,
                    prompt=prompt,
                    verbose=False,
                    memory=memory,
                )
                response = conversation.predict(human_input=user_question)

    return response

