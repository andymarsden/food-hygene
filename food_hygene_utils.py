import streamlit as st
import requests


FOOD_HYGENE_BASE_URL = "https://api.ratings.food.gov.uk"

API_HEADERS = {
    "x-api-version": "2",
    "accept": "application/json",
}

@st.cache_data(ttl=3600)
def get_regions():
    url = FOOD_HYGENE_BASE_URL + "/Regions"
    headers = API_HEADERS
    response = requests.get(url, headers=headers)
    response.raise_for_status() # todo - handle error (lilkey due to timeouts and throttling etc)
    return response.json()

@st.cache_data(ttl=3600)
def get_establishments(laId):
    print(f"/localAuthorityId={laId}")
    url = FOOD_HYGENE_BASE_URL + f"/Establishments?localAuthorityId={laId}"
    headers = API_HEADERS
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=3600)
def get_authorities_basic():
    url = FOOD_HYGENE_BASE_URL+"/Authorities/basic"
    r = requests.get(url, headers=API_HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    
    # Handle either a raw list or an object with 'authorities'
    if isinstance(data, dict) and "authorities" in data:
        return data["authorities"]
    
    return data