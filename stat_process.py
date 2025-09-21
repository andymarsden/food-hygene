import requests
import pandas as pd
import food_hygene_utils as fhu

FOOD_HYGENE_BASE_URL = "https://api.ratings.food.gov.uk"
API_HEADERS = {
    "x-api-version": "2",
    "accept": "application/json",
}

def get_authorities_basic():
    url = FOOD_HYGENE_BASE_URL + "/Authorities/basic"
    r = requests.get(url, headers=API_HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "authorities" in data:
        return data["authorities"]
    return data

def main():
    authorities = get_authorities_basic()
    results = []

    for auth in authorities:
        name = auth.get("Name", "Unknown")
        laId = auth.get("LocalAuthorityId")
        try:
            establishments = fhu.get_establishments(laId)
            if establishments and "establishments" in establishments:
                est_list = establishments["establishments"]
                ratings = [
                    int(e.get("RatingValue"))
                    for e in est_list
                    if str(e.get("RatingValue")).isdigit()
                ]
                if ratings:
                    avg_rating = sum(ratings) / len(ratings)
                    rating_counts = pd.Series(ratings).value_counts().sort_index()
                    counts_str = ", ".join(f"{r}:{rating_counts.get(r,0)}" for r in range(6))
                else:
                    avg_rating = None
                    counts_str = ", ".join(f"{r}:0" for r in range(6))
            else:
                avg_rating = None
                counts_str = ", ".join(f"{r}:0" for r in range(6))
        except Exception as e:
            avg_rating = None
            counts_str = ", ".join(f"{r}:0" for r in range(6))
        results.append(f"{name} (ID: {laId}) | Avg: {avg_rating if avg_rating is not None else 'N/A'} | Counts: {counts_str}")

    # Save results to a text file
    with open("authority_rating_stats.txt", "w") as f:
        for line in results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()