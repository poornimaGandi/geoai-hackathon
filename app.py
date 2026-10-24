import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

from main import run_assistant

st.set_page_config(
    page_title="GeoAI Outdoor Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- THEME --------------------

st.markdown("""
<style>
.stApp { background:#f3f7fa; color:#203447; }
[data-testid="stHeader"] { background:rgba(243,247,250,.95); }
.block-container { padding-top:1.5rem; padding-bottom:2rem; max-width:1500px; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #dce7ed; }
[data-testid="stSidebar"] * { color:#173b52; }
[data-testid="stSidebar"] input { color:#173b52 !important; background:#fff !important; }
[data-testid="stSidebar"] label { font-weight:600; }
[data-testid="stSidebar"] [data-baseweb="select"] * { color:#173b52 !important; }

.hero {
    background:linear-gradient(120deg,#123b55,#167d86,#39a69c);
    padding:30px 32px;
    border-radius:20px;
    color:#fff;
    margin-bottom:22px;
    box-shadow:0 10px 28px #123b551f;
}
.hero h1 {
    color:#fff !important;
    font-size:2.35rem;
    margin:0 0 8px 0;
}
.hero p {
    color:#e8ffff !important;
    font-size:1.03rem;
    margin:0;
}

.stApp h1,.stApp h2,.stApp h3,.stApp h4 {
    color:#173b52 !important;
}
.stApp p,.stApp label,.stApp li {
    color:#344f61;
}

[data-testid="stMetric"] {
    background:#fff;
    border:1px solid #dce7ed;
    border-radius:15px;
    padding:16px 18px;
    box-shadow:0 3px 12px #18375009;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color:#536b7c !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color:#123b55 !important;
}

[data-testid="stAlert"] {
    border-radius:12px;
}
.stButton button,
.stFormSubmitButton button,
[data-testid="stDownloadButton"] button {
    border-radius:10px;
    font-weight:650;
    min-height:2.65rem;
}
[data-testid="stDataFrame"] {
    border:1px solid #dce7ed;
    border-radius:12px;
    overflow:hidden;
}
.section-note {
    color:#647b8b;
    font-size:.92rem;
    margin-top:-8px;
}
.footer {
    text-align:center;
    color:#64788b;
    font-size:.88rem;
    padding:10px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- ACTIVITIES --------------------

ACTIVITIES = [
    "Running",
    "Cycling",
    "Golf",
    "Cricket",
    "Football",
    "Tennis",
    "Hiking",
    "Picnic",
    "Outdoor event",
    "Outdoor photography",
]


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## 🌍 GeoAI")
    st.caption("Your outdoor activity assistant")
    st.divider()

    with st.form("search_form"):
        activity = st.selectbox(
            "Choose activity",
            ACTIVITIES,
        )

        location = st.text_input(
            "Location",
            placeholder="e.g. Rajamahendravaram",
        )

        radius = st.slider(
            "Search radius (km)",
            min_value=1,
            max_value=25,
            value=5,
        )

        submitted = st.form_submit_button(
            "🔎 Find places",
            type="primary",
            width="stretch",
        )

    st.divider()
    st.caption(
        "Discover nearby places using map data "
        "and weather information."
    )
    st.caption(
        "Tip: use a town, city, landmark, or locality name."
    )


# -------------------- HEADER --------------------

st.markdown("""
<div class="hero">
    <h1>Explore the outdoors 🌿</h1>
    <p>
        Discover nearby places, understand current weather,
        and compare options for your next outdoor activity.
    </p>
</div>
""", unsafe_allow_html=True)


# -------------------- RUN SEARCH --------------------

if submitted:

    if not location.strip():
        st.session_state.pop("geoai_result", None)

        st.session_state["geoai_error"] = (
            "Please enter a location before searching."
        )

    else:
        query = (
            f"{activity.lower()} near "
            f"{location.strip()} within {radius} km"
        )

        try:
            with st.spinner(
                "Checking weather and finding nearby places..."
            ):
                result = run_assistant(query)

            if not isinstance(result, dict):
                raise ValueError(
                    "The backend did not return structured results. "
                    "Please check run_assistant() in main.py."
                )

            if not result.get("success"):
                raise ValueError(
                    result.get(
                        "error",
                        "The search could not be completed.",
                    )
                )

            result["_requested_activity"] = activity
            result["_requested_location"] = location.strip()

            st.session_state["geoai_result"] = result
            st.session_state.pop("geoai_error", None)

        except Exception as exc:
            st.session_state["geoai_error"] = str(exc)
            st.session_state.pop("geoai_result", None)


# -------------------- ERROR MESSAGE --------------------

if st.session_state.get("geoai_error"):
    st.error(st.session_state["geoai_error"])


# -------------------- RESULTS --------------------

result = st.session_state.get("geoai_result")

if not result:

    st.info(
        "Choose an activity and enter a location in the sidebar "
        "to view weather, recommendations, charts, and the map."
    )

else:
    weather = result.get("weather") or {}
    places = result.get("places") or []

    result_location = (
        result.get("location")
        or result.get("_requested_location", "your location")
    )

    result_activity = (
        result.get("activity")
        or result.get("_requested_activity", "Outdoor activity")
    )

    result_radius = result.get("radius_km", "—")

    st.markdown(f"### 📍 Exploring {result_location}")

    st.markdown(
        f"<div class='section-note'>"
        f"Activity: <b>{result_activity}</b> &nbsp;·&nbsp; "
        f"Search radius: <b>{result_radius} km</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.write("")


    # -------------------- WEATHER --------------------

    st.subheader("🌤️ Weather snapshot")

    temperature = weather.get("temperature")
    rain = weather.get("rain")
    wind = weather.get("wind")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🌡️ Temperature",
        f"{temperature} °C"
        if temperature is not None
        else "Unavailable",
    )

    c2.metric(
        "🌧️ Rainfall",
        f"{rain} mm"
        if rain is not None
        else "Unavailable",
    )

    c3.metric(
        "💨 Wind speed",
        f"{wind} km/h"
        if wind is not None
        else "Unavailable",
    )


    # -------------------- ACTIVITY SUITABILITY --------------------

    status = str(
        result.get(
            "weather_status",
            "Weather suitability not provided",
        )
    )

    st.subheader("🌱 Activity suitability")

    status_lower = status.lower()

    if any(word in status_lower for word in [
        "not ideal",
        "unsuitable",
        "not suitable",
        "unsafe",
    ]):
        st.warning(f"Weather note: {status}")

    elif any(word in status_lower for word in [
        "suitable",
        "ideal",
        "good",
    ]):
        st.success(f"Weather note: {status}")

    else:
        st.info(status)

    st.caption(
        "Suitability comes from the backend assessment; "
        "check local conditions before heading outdoors."
    )


    # -------------------- RECOMMENDATIONS --------------------

    df = pd.DataFrame(places)

    st.divider()
    st.subheader("📊 Nearby recommendations")

    if df.empty:

        st.info(
            "No matching places were returned. "
            "Try another location or increase the search radius."
        )

    else:
        required = {
            "name",
            "distance_km",
            "latitude",
            "longitude",
        }

        missing = required - set(df.columns)

        if missing:
            st.error(
                "Some required place details are missing "
                "from the backend response: "
                + ", ".join(sorted(missing))
            )

        else:
            df["distance_km"] = pd.to_numeric(
                df["distance_km"],
                errors="coerce",
            )

            df["latitude"] = pd.to_numeric(
                df["latitude"],
                errors="coerce",
            )

            df["longitude"] = pd.to_numeric(
                df["longitude"],
                errors="coerce",
            )

            df["name"] = (
                df["name"]
                .fillna("Unnamed place")
                .astype(str)
            )

            df = df.dropna(subset=["distance_km"])
            df = df[df["distance_km"] >= 0].copy()

            if df.empty:
                st.info(
                    "The backend returned no places "
                    "with usable distance values."
                )

            else:

                # -------------------- FILTERS --------------------

                type_col = next(
                    (
                        col for col in [
                            "type",
                            "category",
                            "place_type",
                            "amenity",
                        ]
                        if col in df.columns
                    ),
                    None,
                )

                f1, f2, f3 = st.columns([1.15, 1.4, 1.1])

                with f1:
                    if type_col:
                        type_values = sorted(
                            df[type_col]
                            .fillna("Unclassified")
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        selected_types = st.multiselect(
                            "Place type",
                            type_values,
                            default=type_values,
                        )

                    else:
                        selected_types = None

                        st.caption(
                            "Place-type filter unavailable because "
                            "the backend returned no type/category field."
                        )

                try:
                    radius_cap = float(result_radius)
                except (TypeError, ValueError):
                    radius_cap = float(df["distance_km"].max())

                slider_max = max(
                    1.0,
                    min(
                        25.0,
                        max(
                            float(df["distance_km"].max()),
                            radius_cap,
                        ),
                    ),
                )

                with f2:
                    distance_limit = st.slider(
                        "Maximum distance (km)",
                        min_value=0.0,
                        max_value=slider_max,
                        value=min(slider_max, radius_cap),
                        step=0.5,
                    )

                with f3:
                    sort_order = st.selectbox(
                        "Sort recommendations",
                        [
                            "Nearest first",
                            "Farthest first",
                            "Place name A–Z",
                        ],
                    )


                # -------------------- APPLY FILTERS --------------------

                filtered = df[
                    df["distance_km"] <= distance_limit
                ].copy()

                if type_col and selected_types is not None:
                    filtered = filtered[
                        filtered[type_col]
                        .fillna("Unclassified")
                        .astype(str)
                        .isin(selected_types)
                    ]

                if sort_order == "Nearest first":
                    filtered = filtered.sort_values(
                        "distance_km",
                        ascending=True,
                    )

                elif sort_order == "Farthest first":
                    filtered = filtered.sort_values(
                        "distance_km",
                        ascending=False,
                    )

                else:
                    filtered = filtered.sort_values(
                        "name",
                        key=lambda s: s.str.lower(),
                    )


                # -------------------- SUMMARY METRICS --------------------

                m1, m2, m3 = st.columns(3)

                m1.metric(
                    "Places returned",
                    len(df),
                )

                m2.metric(
                    "Places after filters",
                    len(filtered),
                )

                m3.metric(
                    "Nearest option",
                    (
                        f"{filtered['distance_km'].min():.2f} km"
                        if not filtered.empty
                        else "—"
                    ),
                )


                if filtered.empty:

                    st.warning(
                        "No places match these filters. "
                        "Increase the distance or select more place types."
                    )

                else:

                    # -------------------- DISTANCE CHART --------------------

                    st.markdown("#### 📊 Distance comparison")
                    st.caption(
                        "Compare how far each recommended place is from your location."
                    )

                    chart_df = filtered.sort_values(
                        "distance_km",
                        ascending=True,
                    ).copy()

                    fig = px.bar(
                        chart_df,
                        x="distance_km",
                        y="name",
                        orientation="h",
                        text="distance_km",
                        labels={
                            "distance_km": "Distance (km)",
                            "name": "Nearby place",
                        },
                        color="distance_km",
                        color_continuous_scale=[
                            "#8EDBD0",
                            "#239A9D",
                            "#123B55",
                        ],
                        hover_data={
                            "distance_km": ":.2f",
                            "latitude": False,
                            "longitude": False,
                        },
                    )

                    fig.update_traces(
                        texttemplate="%{text:.2f} km",
                        textposition="outside",
                        textfont=dict(
                            color="#173B52",
                            size=12,
                        ),
                        cliponaxis=False,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Distance: %{x:.2f} km"
                            "<extra></extra>"
                        ),
                    )

                    fig.update_layout(
                        template="plotly_white",
                        height=max(400, 48 * len(chart_df)),
                        paper_bgcolor="#F3F7FA",
                        plot_bgcolor="#FFFFFF",
                        font=dict(
                            family="Arial",
                            size=13,
                            color="#173B52",
                        ),
                        coloraxis_showscale=False,
                        margin=dict(
                            l=20,
                            r=100,
                            t=25,
                            b=60,
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Distance (km)",
                                font=dict(color="#173B52", size=14),
                            ),
                            tickfont=dict(color="#334F61", size=12),
                            gridcolor="#DCE7ED",
                            zeroline=False,
                        ),
                        yaxis=dict(
                            title="",
                            tickfont=dict(color="#173B52", size=12),
                            automargin=True,
                            categoryorder="array",
                            categoryarray=chart_df["name"].tolist(),
                        ),
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        key="distance_comparison_chart",
                    )

                    # -------------------- SECOND VISUALIZATION --------------------

                    st.markdown("#### 📈 Recommendation overview")

                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        # How many places are within each distance range?
                        bins = [0, 1, 3, 5, 10, float("inf")]
                        labels = [
                            "0–1 km",
                            "1–3 km",
                            "3–5 km",
                            "5–10 km",
                            "10+ km",
                        ]

                        overview_df = filtered.copy()

                        overview_df["Distance range"] = pd.cut(
                            overview_df["distance_km"],
                            bins=bins,
                            labels=labels,
                            right=True,
                            include_lowest=True,
                        )

                        range_counts = (
                            overview_df["Distance range"]
                            .value_counts(sort=False)
                            .reindex(labels, fill_value=0)
                            .rename_axis("Distance range")
                            .reset_index(name="Number of places")
                        )

                        range_fig = px.bar(
                            range_counts,
                            x="Distance range",
                            y="Number of places",
                            text="Number of places",
                            color="Number of places",
                            color_continuous_scale=[
                                "#B9E5DD",
                                "#167D86",
                                "#123B55",
                            ],
                        )

                        range_fig.update_traces(
                            textposition="outside",
                            textfont=dict(color="#173B52"),
                        )

                        range_fig.update_layout(
                            template="plotly_white",
                            title="Places by distance range",
                            height=350,
                            paper_bgcolor="#FFFFFF",
                            plot_bgcolor="#FFFFFF",
                            font=dict(color="#173B52", size=12),
                            coloraxis_showscale=False,
                            margin=dict(l=15, r=15, t=60, b=40),
                            xaxis=dict(
                                title="Distance range",
                                tickfont=dict(color="#334F61"),
                            ),
                            yaxis=dict(
                                title="Number of places",
                                tickfont=dict(color="#334F61"),
                                gridcolor="#DCE7ED",
                            ),
                        )

                        st.plotly_chart(
                            range_fig,
                            use_container_width=True,
                            key="distance_range_chart",
                        )

                    with chart_col2:
                        # Show the distribution of place categories, if available.
                        if type_col:
                            category_df = (
                                filtered[type_col]
                                .fillna("Unclassified")
                                .astype(str)
                                .value_counts()
                                .rename_axis("Place type")
                                .reset_index(name="Number of places")
                            )

                            category_fig = px.pie(
                                category_df,
                                names="Place type",
                                values="Number of places",
                                hole=0.55,
                                color_discrete_sequence=[
                                    "#123B55",
                                    "#167D86",
                                    "#39A69C",
                                    "#8EDBD0",
                                    "#F4B860",
                                    "#D97757",
                                ],
                            )

                            category_fig.update_traces(
                                textposition="inside",
                                textinfo="percent+label",
                                insidetextfont=dict(
                                    color="#FFFFFF",
                                    size=11,
                                ),
                                hovertemplate=(
                                    "<b>%{label}</b><br>"
                                    "Places: %{value}<br>"
                                    "Share: %{percent}"
                                    "<extra></extra>"
                                ),
                            )

                            category_fig.update_layout(
                                title="Places by category",
                                height=350,
                                paper_bgcolor="#FFFFFF",
                                font=dict(
                                    color="#173B52",
                                    size=12,
                                ),
                                margin=dict(l=15, r=15, t=60, b=20),
                                legend=dict(
                                    font=dict(color="#173B52"),
                                ),
                            )

                            st.plotly_chart(
                                category_fig,
                                use_container_width=True,
                                key="place_category_chart",
                            )

                        else:
                            st.info(
                                "A category chart will appear when the "
                                "backend provides place types. The distance "
                                "range chart is available without categories."
                            )



                    # -------------------- INTERACTIVE MAP --------------------

                    st.markdown("#### 🗺️ Interactive places map")

                    map_df = filtered.dropna(
                        subset=["latitude", "longitude"]
                    ).copy()

                    map_df = map_df[
                        map_df["latitude"].between(-90, 90)
                        & map_df["longitude"].between(-180, 180)
                    ]

                    if not map_df.empty:

                        layer = pdk.Layer(
                            "ScatterplotLayer",
                            data=map_df,
                            get_position="[longitude, latitude]",
                            get_radius=110,
                            get_fill_color=[22, 125, 134, 220],
                            get_line_color=[18, 59, 85, 255],
                            line_width_min_pixels=1,
                            pickable=True,
                            auto_highlight=True,
                        )

                        view = pdk.ViewState(
                            latitude=float(
                                map_df["latitude"].mean()
                            ),
                            longitude=float(
                                map_df["longitude"].mean()
                            ),
                            zoom=11,
                            pitch=0,
                        )

                        deck = pdk.Deck(
                            layers=[layer],
                            initial_view_state=view,
                            tooltip={
                                "text": "{name}\nDistance: {distance_km} km"
                            },
                            map_style="light",
                        )

                        st.pydeck_chart(
                            deck,
                            width="stretch",
                        )

                        st.caption(
                            "Map markers show the filtered results; "
                            "hover/select a marker to inspect its details "
                            "where supported."
                        )

                    else:
                        st.info(
                            "The filtered places do not have "
                            "valid map coordinates."
                        )


                    # -------------------- PLACE DETAILS --------------------

                    st.markdown("#### 📋 Place details")

                    display_cols = [
                        c for c in [
                            "name",
                            type_col,
                            "distance_km",
                            "latitude",
                            "longitude",
                        ]
                        if c and c in filtered.columns
                    ]

                    display_df = filtered[display_cols].rename(
                        columns={
                            "name": "Place",
                            "distance_km": "Distance (km)",
                            "latitude": "Latitude",
                            "longitude": "Longitude",
                        }
                    )

                    st.dataframe(
                        display_df,
                        width="stretch",
                        hide_index=True,
                    )


                    # -------------------- CSV DOWNLOAD --------------------

                    st.download_button(
                        "⬇️ Download filtered recommendations (CSV)",
                        data=filtered.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="geoai_recommendations.csv",
                        mime="text/csv",
                    )


# -------------------- FOOTER --------------------

st.divider()

st.markdown(
    "<div class='footer'>"
    "GeoAI Outdoor Assistant · OpenStreetMap · "
    "Open-Meteo · Local SLM"
    "</div>",
    unsafe_allow_html=True,
)