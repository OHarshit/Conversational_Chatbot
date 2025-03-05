from rapidfuzz import process
import pandas as pd
import re
import json
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
    return base_url

    
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