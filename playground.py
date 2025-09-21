import requests

#region constants

FOOD_HYGENE_BASE_URL = "https://api.ratings.food.gov.uk"

#endregion

#region API Config

API_HEADERS = {
    "x-api-version": "2",
    "accept": "application/json",
}

#endregion


def get_establishments(laId):
    print(f"/localAuthorityId={laId}")

    url = FOOD_HYGENE_BASE_URL + f"/Establishments?localAuthorityId={laId}"
    headers = API_HEADERS
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

establishments = get_establishments(406)