import os
import numpy as np
from scipy.stats import ttest_ind

stats_file = "authority_rating_stats.txt"

def get_uk_average():
    if os.path.exists(stats_file):
        with open(stats_file) as f:
            lines = f.readlines()
        # Extract averages, ignoring 'N/A'
        avgs = []
        for line in lines:
            if "| Avg:" in line:
                avg_part = line.split("| Avg:")[1].split("|")[0].strip()
                try:
                    avg = float(avg_part)
                    avgs.append(avg)
                except ValueError:
                    continue
        if avgs:
            return sum(avgs) / len(avgs)
            #st.info(f"**Overall Average Rating Across All Authorities:** {overall_avg:.2f}")
        else:
            return None
            #st.warning("No valid average ratings found in stats file.")
    else:
        return None
        #st.warning("Stats file not found. Please run the calculation script first.")

def get_la_average(establishments):
    """
    Calculate the average hygiene rating for a single local authority (LA).
    Only considers numeric ratings (0-5).
    """
    if not establishments or "establishments" not in establishments:
        return None
    ratings = [
        int(e.get("RatingValue"))
        for e in establishments["establishments"]
        if str(e.get("RatingValue")).isdigit()
    ]
    if ratings:
        return sum(ratings) / len(ratings)
    return None

def compare_la_to_uk(la_ratings, uk_ratings, alpha=0.05):
    """
    Compare LA average to UK average using a t-test.
    Returns "worse", "approx the same", or "better".
    - la_ratings: list of numeric ratings for the LA
    - uk_ratings: list of numeric ratings for the UK
    - alpha: significance level (default 0.05)
    """
    # Ensure both lists have data
    if not la_ratings or not uk_ratings:
        return "approx the same"
    # t-test (two-sided)
    t_stat, p_value = ttest_ind(la_ratings, uk_ratings, equal_var=False, nan_policy='omit')
    la_mean = np.mean(la_ratings)
    uk_mean = np.mean(uk_ratings)
    if p_value < alpha:
        if la_mean < uk_mean:
            return "worse"
        else:
            return "better"
    else:
        return "approx the same"


def get_best_and_worst_la():
    """
    Returns a tuple: (best_la_name, best_avg, worst_la_name, worst_avg)
    based on average ratings in authority_rating_stats.txt.
    """
    if not os.path.exists(stats_file):
        return None, None, None, None

    best_la = None
    best_avg = -float("inf")
    worst_la = None
    worst_avg = float("inf")

    with open(stats_file) as f:
        for line in f:
            if "| Avg:" in line:
                name = line.split(" (ID:")[0].strip()
                avg_part = line.split("| Avg:")[1].split("|")[0].strip()
                try:
                    avg = float(avg_part)
                except ValueError:
                    continue
                if avg > best_avg:
                    best_avg = avg
                    best_la = name
                if avg < worst_avg:
                    worst_avg = avg
                    worst_la = name

    return best_la, best_avg, worst_la, worst_avg