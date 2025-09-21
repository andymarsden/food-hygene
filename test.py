# streamlit run /workspaces/food-hygene/test.py
import streamlit as st
import requests
import pandas as pd
import food_hygene_utils as fhu
import stats_utils as su

#region TODOs

# AM - proper error handling around raise_for_status() - prefer my usaul verbose way but this is quicker.
# AM - add map with geocoded establishments - done
# AM - add bar chart of ratings distribution - done
# AM - add comparison to UK average - done
# AM - add best and worst local authority - done

# AM - Sort default select
# AM - add university locations to map as selectable points of interest - doing

# AM - Birmingham LA seems to be only including 5s!!!

#endregion

st.title("Food Hygiene Rating Scheme")

try:
    authorities = fhu.get_authorities_basic()

    # maybe use lambda here instead of another function?

    def show_authority_name(authority):
        return authority.get("Name", "Unknown")
    
    # show default of Lincoln City
    # bit hacky but works
    default_index = 0
    for i, auth in enumerate(authorities):
        if "lincoln city" in auth.get("Name", "").lower():
            default_index = i
        break

    selected = st.selectbox(
        "Choose an authority",
        options=authorities,
        format_func=show_authority_name,
        index=default_index # default to Lincoln City
    )
    if selected:
        laId = selected.get("LocalAuthorityId")
        st.write("**Selected Authority ID:**", laId)
        #st.json(selected)

        # establishments = get_establishments(laId)
        establishments = fhu.get_establishments(laId)

        # st.write(establishments)
        # st.json(establishments)

        overall_avg = su.get_uk_average()
        st.info(f"**Overall Average Rating Across All Authorities:** {overall_avg:.2f}")
        
        la_avg = su.get_la_average(establishments)
        if la_avg is not None:
            st.success(f"**Average Rating for {selected.get('Name', 'Selected Authority')}:** {la_avg:.2f}")
        else:
            st.warning(f"No valid ratings found for {selected.get('Name', 'Selected Authority')}.")
        
        # la_uk_comparison = su.compare_la_to_uk(la_avg,overall_avg)
        # st.info(f"**Comparison to UK Average:** {la_uk_comparison}")


        best_la, best_avg, worst_la, worst_avg = su.get_best_and_worst_la()
        if best_la and worst_la:
            st.success(f"**Best Local Authority:** {best_la} (Average Rating: {best_avg:.2f})")
            st.error(f"**Worst Local Authority:** {worst_la} (Average Rating: {worst_avg:.2f})")
        else:
            st.warning("Could not determine best and worst local authorities. Make sure the stats file exists")

        # simple summary chart (ratings distribution)
        if establishments and "establishments" in establishments:
            est_list = establishments["establishments"]
            # Extract RatingValue and count occurrences
            ratings = [e.get("RatingValue", "Unknown") for e in est_list]
            
            #ratings_count = pd.Series(ratings).value_counts()
            ratings_count = pd.Series(ratings).value_counts().sort_index() #sort 0-5

            st.subheader("Hygiene Ratings Distribution")
            st.bar_chart(ratings_count)

#region map

            # Filter for establishments with valid geocode - none geocodes messes ip here.
            map_data = []
            for e in est_list:
                geo = e.get("geocode", {})
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat and lon:
                    try:
                        lat_f = float(lat)
                        lon_f = float(lon)
                        map_data.append({
                            "BusinessName": e.get("BusinessName", ""),
                            "RatingValue": e.get("RatingValue", ""),
                            "latitude": lat_f,
                            "longitude": lon_f,
                        })
                    except Exception:
                        continue

            if map_data:
                df_map = pd.DataFrame(map_data)
                st.subheader("Establishments Map")

                import pydeck as pdk

                #colors
                rating_colors = {
                    "0": [128, 0, 0, 160],    # dark red
                    "1": [255, 0, 0, 160],    # red
                    "2": [255, 128, 0, 160],  # orange
                    "3": [255, 255, 0, 160],  # yellow
                    "4": [0, 128, 255, 160],   # blue
                    "5":  [0, 200, 0, 160],  # green
                }
                # Add color column to df
                def get_color(rating):
                    return rating_colors.get(str(rating), [255, 105, 180, 160])  # pink for others

                df_map["color"] = df_map["RatingValue"].apply(get_color)

                # layer = pdk.Layer(
                #     "ScatterplotLayer",
                #     data=df_map,
                #     get_position='[longitude, latitude]',
                #     get_color="color",
                #     get_radius=60,
                #     pickable=True,
                # )
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=df_map,
                    get_position='[longitude, latitude]',
                    get_color="color",
                    get_radius=60,
                    pickable=True,
                    radius_min_pixels=2, 
                    radius_max_pixels=6,
                    radius_scale=1, # dont sclale with zoom - looked odd with big circles
                )

                tooltip = {
                    "html": "<b>{BusinessName}</b><br>Rating: {RatingValue}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }

                st.pydeck_chart(
                    pdk.Deck(
                        layers=[layer],
                        initial_view_state=pdk.ViewState(
                            latitude=df_map["latitude"].mean(),
                            longitude=df_map["longitude"].mean(),
                            zoom=11,
                            pitch=0,
                        ),
                        tooltip=tooltip,
                    )
                )
#endregion map
                

#region type v rating chart
 # --- BusinessType vs Rating chart (horizontal 100% stacked, numeric ratings only, ordered by % of 5s) ---
        if establishments and "establishments" in establishments:
            est_list = establishments["establishments"]
            # Create DataFrame for analysis
            df_bt = pd.DataFrame([
                {
                    "BusinessType": e.get("BusinessType", "Unknown"),
                    "RatingValue": e.get("RatingValue", "Unknown")
                }
                for e in est_list
            ])
            # Only keep numeric ratings (0-5)
            df_bt = df_bt[df_bt["RatingValue"].isin([str(i) for i in range(6)])]

            # Count of each rating per business type
            bt_rating_counts = (
                df_bt.groupby(["BusinessType", "RatingValue"])
                .size()
                .reset_index(name="Count")
            )

            # Calculate total per BusinessType for percentage
            total_per_type = bt_rating_counts.groupby("BusinessType")["Count"].transform("sum")
            bt_rating_counts["Percent"] = bt_rating_counts["Count"] / total_per_type * 100

            # Calculate % of establishments rated 5 for ordering
            percent_5 = bt_rating_counts[bt_rating_counts["RatingValue"] == "5"][["BusinessType", "Percent"]]
            percent_5 = percent_5.set_index("BusinessType")["Percent"]

            # Set BusinessType as categorical ordered by % of 5s descending
            bt_rating_counts["BusinessType"] = pd.Categorical(
                bt_rating_counts["BusinessType"],
                categories=percent_5.sort_values(ascending=False).index,
                ordered=True
            )

            import plotly.express as px
            st.subheader("Business Type vs Hygiene Rating (Horizontal 100% Stacked, Ordered by % of 5s)")
            fig = px.bar(
                bt_rating_counts,
                y="BusinessType",
                x="Percent",
                color="RatingValue",
                orientation="h",
                barmode="stack",
                labels={
                    "Percent": "Percentage of Establishments",
                    "BusinessType": "Business Type",
                    "RatingValue": "Rating"
                },
                title="100% Stacked: Relationship between Business Type and Hygiene Rating (Ordered by % of 5s)"
            )
            fig.update_layout(
                yaxis={'categoryorder':'array'},
                xaxis_tickformat=".0f%%"
            )
            st.plotly_chart(fig, use_container_width=True)


#rendregion



except Exception as e:
    st.error(f"Error Occured: {e}")






# try:
#     regions = get_regions()
#     st.success("Regions loaded successfully!")

#     # Display as table
#     st.subheader("Regions Table")
#     st.table(regions)

#     # Or list them one by one
#     st.subheader("Regions List")
#     for region in regions:
#         st.write(f"**{region['Id']}** – {region['Name']}")

# except Exception as e:
#     st.error(f"Failed to fetch regions: {e}")