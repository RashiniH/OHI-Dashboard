import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.markdown("""
<style>
/* Increase tab font */
button[data-baseweb="tab"] {
    font-size: 18px !important;
    font-weight: 600;
}

/* Active tab highlight */
button[data-baseweb="tab"][aria-selected="true"] {
    color: #1D9E75 !important;
    border-bottom: 3px solid #1D9E75 !important;
}

/* Add spacing */
div[role="tablist"] {
    gap: 20px;
}
</style>
""", unsafe_allow_html=True)

# Page config 
st.set_page_config(
    page_title="Ocean Health Index Dashboard",
    page_icon="🌊",
    layout="wide",
)

# Load & prepare data
@st.cache_data
def load_data():
    df = pd.read_csv("OHI_OHI_WIDEF.csv")
    year_cols = [str(y) for y in range(2012, 2025)]
    df_long = df.melt(
        id_vars=["REF_AREA", "REF_AREA_LABEL"],
        value_vars=year_cols,
        var_name="Year",
        value_name="OHI_Score",
    )
    df_long["Year"] = df_long["Year"].astype(int)
    df_long = df_long.sort_values(["REF_AREA_LABEL", "Year"]).reset_index(drop=True)
    return df_long

df = load_data()

# Sidebar 
st.sidebar.title("🌊 OHI Dashboard")
st.sidebar.markdown("**Ocean Health Index**  \nGlobal Sustainability Explorer")
st.sidebar.divider()

all_years   = sorted(df["Year"].unique())
all_countries = sorted(df["REF_AREA_LABEL"].unique())

selected_year = st.sidebar.slider(
    "Select Year",
    min_value=int(min(all_years)),
    max_value=int(max(all_years)),
    value=2024,
    step=1,
)

selected_countries = st.sidebar.multiselect(
    "Compare Countries",
    options=all_countries,
    default=["Australia", "United Kingdom", "China", "Brazil", "India"],
)

st.sidebar.divider()
st.sidebar.markdown(
    "**Data Source:** [Ocean Health Index](https://oceanhealthindex.org)  \n"
    "**Provider:** World Bank Data360  \n"
    "**Coverage:** 194 countries · 2012–2024"
)

#  Header 
st.title("🌊 Ocean Health Index - Global Sustainability Dashboard")
st.markdown(
    "Analysing the sustainable use of ocean resources across **194 countries** "
    "from 2012 to 2024. Scores range from 0 (poor) to 100 (excellent), aligned "
    "with **UN SDG 14: Life Below Water**."
)
st.divider()

# KPI cards

year_df  = df[df["Year"] == selected_year]
prev_df  = df[df["Year"] == selected_year - 1]

global_avg = round(year_df["OHI_Score"].mean(), 2)

if not prev_df.empty:
    prev_avg = round(prev_df["OHI_Score"].mean(), 2)
    delta_avg = round(global_avg - prev_avg, 2)
else:
    delta_avg = 0

best_country    = year_df.loc[year_df["OHI_Score"].idxmax(), "REF_AREA_LABEL"]
best_score      = round(year_df["OHI_Score"].max(), 2)

worst_country   = year_df.loc[year_df["OHI_Score"].idxmin(), "REF_AREA_LABEL"]
worst_score     = round(year_df["OHI_Score"].min(), 2)

countries_above = int((year_df["OHI_Score"] >= 70).sum())

k1, k2, k3, k4 = st.columns(4)
k1.metric("🌍 Global Average Score", f"{global_avg}/100", delta=f"{delta_avg} vs {selected_year-1}")
k2.metric("🏆 Highest Score", best_country, f"{best_score}/100")
k3.metric("⚠️ Lowest Score",  worst_country, f"{worst_score}/100")
k4.metric("✅ Countries Scoring ≥70", f"{countries_above} / {len(year_df)}")

st.divider()

# Tab layout 
tab1, tab2 = st.tabs([
    "🗺️ Global Overview",
    "🔍 Country Deep Dive",
])

# TAB 1 — Global Overview (World Map + Trends + Score Distribution)
with tab1:
    #  World Map
    st.subheader(f"Global OHI Scores - {selected_year}")
    st.markdown(
    "Hover over any country to see its score. "

    "Darker green = healthier ocean"
    
    "Darker red = lower sustainability"
    )

    fig_map = px.choropleth(
        year_df,
        locations="REF_AREA",
        locationmode="ISO-3",
        color="OHI_Score",
        hover_name="REF_AREA_LABEL",
        hover_data={"OHI_Score": ":.1f", "REF_AREA": False},
        color_continuous_scale=[
            [0.0,  "#b22222"],
            [0.4,  "#ff8c00"],
            [0.6,  "#ffd700"],
            [0.75, "#90ee90"],
            [1.0,  "#006400"],
        ],
        range_color=[46, 87],
        labels={"OHI_Score": "OHI Score"},
        title=f"Ocean Health Index Scores by Country ({selected_year})",
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title="Score (0–100)"),
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
        height=500,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.divider()

    #  Trends side by side 
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Global Average OHI Score - 2012 to 2024")
        global_trend = df.groupby("Year")["OHI_Score"].mean().reset_index()
        global_trend.columns = ["Year", "Average OHI Score"]

        fig_trend = px.line(
            global_trend,
            x="Year",
            y="Average OHI Score",
            markers=True,
            title="Global Average Ocean Health Index (2012–2024)",
            labels={"Average OHI Score": "Average OHI Score (0–100)"},
            color_discrete_sequence=["#1D9E75"],
        )
        fig_trend.add_hline(y=70, line_dash="dash", line_color="orange",
                            annotation_text="Sustainability threshold (70)",
                            annotation_position="bottom right")
        fig_trend.update_layout(height=380, xaxis=dict(dtick=1))
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("Country Comparison Over Time")
        if selected_countries:
            comp_df = df[df["REF_AREA_LABEL"].isin(selected_countries)]
            fig_comp = px.line(
                comp_df,
                x="Year",
                y="OHI_Score",
                color="REF_AREA_LABEL",
                markers=True,
                title="OHI Score Trends - Selected Countries",
                labels={"OHI_Score": "OHI Score (0–100)", "REF_AREA_LABEL": "Country"},
            )
            fig_comp.add_hline(y=70, line_dash="dash", line_color="orange",
                               annotation_text="Score of 70",
                               annotation_position="bottom right")
            fig_comp.update_layout(height=380, xaxis=dict(dtick=1))
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Select countries in the sidebar to compare their trends.")

    st.divider()

    #  Score Distribution 
    st.subheader(f"Score Distribution - {selected_year}")
    fig_hist = px.histogram(
        year_df,
        x="OHI_Score",
        nbins=20,
        title=f"Distribution of OHI Scores Across All Countries ({selected_year})",
        labels={"OHI_Score": "OHI Score (0–100)", "count": "Number of Countries"},
        color_discrete_sequence=["#1D9E75"],
    )
    fig_hist.add_vline(x=global_avg, line_dash="dash", line_color="#0F6E56",
                       annotation_text=f"Global avg: {global_avg}",
                       annotation_position="top right")
    fig_hist.update_layout(height=350)
    st.plotly_chart(fig_hist, use_container_width=True)

# TAB 2 - Country Deep Dive
with tab2:
    st.subheader("Country Deep Dive")

    selected_single = st.selectbox(
        "Select a country to explore",
        options=all_countries,
        index=all_countries.index("United Kingdom") if "United Kingdom" in all_countries else 0,
    )

    country_df = df[df["REF_AREA_LABEL"] == selected_single]
    latest_score = country_df[country_df["Year"] == selected_year]["OHI_Score"].values
    latest_score = round(float(latest_score[0]), 2) if len(latest_score) > 0 else "N/A"

    first_score  = round(float(country_df[country_df["Year"] == 2012]["OHI_Score"].values[0]), 2)
    last_score   = round(float(country_df[country_df["Year"] == 2024]["OHI_Score"].values[0]), 2)
    change       = round(last_score - first_score, 2)
    rank_in_year = int(year_df["OHI_Score"].rank(ascending=False)[year_df["REF_AREA_LABEL"] == selected_single].values[0])

    d1, d2, d3, d4 = st.columns(4)
    d1.metric(f"Score in {selected_year}", f"{latest_score}/100")
    d2.metric("Score in 2012", f"{first_score}/100")
    d3.metric("Change 2012→2024", f"{change:+.2f}")
    d4.metric(f"Global Rank ({selected_year})", f"#{rank_in_year} of 194")

    fig_single = px.line(
        country_df,
        x="Year",
        y="OHI_Score",
        markers=True,
        title=f"OHI Score Over Time — {selected_single}",
        labels={"OHI_Score": "OHI Score (0–100)"},
        color_discrete_sequence=["#185FA5"],
    )
    global_avg_line = df.groupby("Year")["OHI_Score"].mean().reset_index()
    fig_single.add_scatter(
        x=global_avg_line["Year"],
        y=global_avg_line["OHI_Score"],
        mode="lines",
        name="Global Average",
        line=dict(dash="dash", color="gray"),
    )
    fig_single.add_hline(y=70, line_dash="dot", line_color="orange",
                         annotation_text="Score of 70")
    fig_single.update_layout(height=400, xaxis=dict(dtick=1))
    st.plotly_chart(fig_single, use_container_width=True)

    st.markdown(f"### Key Insight for {selected_single}")
    if change > 0:
        direction = f"improved by **{change} points**"
        emoji = "📈"
    else:
        direction = f"declined by **{abs(change)} points**"
        emoji = "📉"

    above_below = "above" if last_score >= global_avg else "below"
    st.info(
        f"{emoji} **{selected_single}** has {direction} between 2012 and 2024. "
        f"Its latest score of **{last_score}/100** is {above_below} the global average of **{global_avg}/100**, "
        f"ranking **#{rank_in_year}** out of 194 countries in {selected_year}."
    )

#  Footer 
st.divider()
st.caption(
    "Dashboard built for 5DATA004C Data Science Project Lifecycle | "
    "Data: Ocean Health Index (OHI) via World Bank Data360 | "
    "Coverage: 194 countries (2012–2024) | "
    "Scores range 0–100 aligned with UN SDG 14: Life Below Water | "
    "Last updated: 2024"
)
