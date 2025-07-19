import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/SatBalakumar/ncaa-basketball-tempo-playstyle-dashboard/refs/heads/main/dashboard/team_AllSeasons_df_test.csv"
    return pd.read_csv(url)

df = load_data()

# ---------------------------
# Rename Columns for UI Clarity
# ---------------------------
rename_map = {
    "season": "Season",
    "team_name": "Team",
    "conference": "Conference",
    "adjusted_tempo_rating": "Tempo",
    "adjusted_offensive_efficiency_rating": "OffEff",
    "adjusted_defensive_efficiency_rating": "DefEff",
    "three_point_share_offense": "O3PT_Share",
    "two_point_share_offense": "O2PT_Share",
    "ft_point_share_offense": "OFT_Share",
    "three_point_share_defense": "D3PT_Share",
    "two_point_share_defense": "D2PT_Share",
    "ft_point_share_defense": "DFT_Share",
    "playstyle_name": "Playstyle_Cluster",
    "avgHeightOnCourt_MinutesWeighted": "AvgHeight"
}
df.rename(columns=rename_map, inplace=True)

# Rename rank columns dynamically
df.columns = df.columns.str.replace("three_point_share_offense_rank", "O3PT_Share_rank")
df.columns = df.columns.str.replace("two_point_share_offense_rank", "O2PT_Share_rank")
df.columns = df.columns.str.replace("ft_point_share_offense_rank", "OFT_Share_rank")
df.columns = df.columns.str.replace("three_point_share_defense_rank", "D3PT_Share_rank")
df.columns = df.columns.str.replace("two_point_share_defense_rank", "D2PT_Share_rank")
df.columns = df.columns.str.replace("ft_point_share_defense_rank", "DFT_Share_rank")

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("Filters")

# Season filter
all_seasons = sorted(df["Season"].unique())
seasons = st.sidebar.multiselect("Select Season(s):", all_seasons, default=all_seasons)

# Conference filter
all_conferences = sorted(df["Conference"].unique())
if "previous_conferences" not in st.session_state:
    st.session_state.previous_conferences = ["big_ten"]
if "selected_teams" not in st.session_state:
    st.session_state.selected_teams = []

conferences = st.sidebar.multiselect("Select Conference(s):", all_conferences, default=st.session_state.previous_conferences)

# Auto-add teams for new conferences
if set(conferences) != set(st.session_state.previous_conferences):
    added_confs = set(conferences) - set(st.session_state.previous_conferences)
    if added_confs:
        new_teams = df[df["Conference"].isin(added_confs)]["Team"].unique().tolist()
        st.session_state.selected_teams = list(set(st.session_state.selected_teams) | set(new_teams))
    st.session_state.previous_conferences = conferences

# Teams belonging to selected conferences
teams_in_selected_conf = sorted(df[df["Conference"].isin(conferences)]["Team"].unique())

# Checkbox to select all teams
select_all_teams = st.sidebar.checkbox("Select All Teams from Selected Conferences", value=False)
if select_all_teams:
    teams = teams_in_selected_conf
else:
    teams = st.sidebar.multiselect("Select Team(s):", teams_in_selected_conf, default=st.session_state.selected_teams)

# Additional teams from other conferences
extra_teams = st.sidebar.multiselect("Add Teams (from other conferences):", sorted(df["Team"].unique()))
teams = list(set(teams + extra_teams))

# Coach Change filter
coach_change = st.sidebar.selectbox("Coach Change:", ["All", "Yes", "No"])

# ---------------------------
# Playstyle Cluster Toggles
# ---------------------------
st.sidebar.markdown("### Playstyle Clusters")
cluster_list = sorted(df["Playstyle_Cluster"].dropna().unique())
cluster_colors = px.colors.qualitative.Set2
color_map = {cluster: cluster_colors[i % len(cluster_colors)] for i, cluster in enumerate(cluster_list)}

active_clusters = []
for cluster in cluster_list:
    cols = st.sidebar.columns([0.2, 0.8])
    with cols[0]:
        st.markdown(f"<div style='color:{color_map[cluster]}; font-size:22px;'>●</div>", unsafe_allow_html=True)
    with cols[1]:
        checked = st.checkbox(cluster, value=True, key=f"cluster_{cluster}")
        if checked:
            active_clusters.append(cluster)

# ---------------------------
# Apply Filters
# ---------------------------
filtered_df = df[(df["Season"].isin(seasons)) & (df["Conference"].isin(conferences)) & (df["Team"].isin(teams))]
if coach_change != "All":
    filtered_df = filtered_df[filtered_df["CoachChange"] == (1 if coach_change == "Yes" else 0)]

filtered_clusters_df = filtered_df[filtered_df["Playstyle_Cluster"].isin(active_clusters)]

# ---------------------------
# Download Button
# ---------------------------
st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_data.csv",
    mime="text/csv"
)

# ---------------------------
# KPI Metrics
# ---------------------------
st.title("Tempo, Playstyle, and Winning Patterns")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Avg Tempo", f"{round(filtered_df['Tempo'].mean(), 2)}")
kpi2.metric("Avg Win%", f"{round(filtered_df['win_pct'].mean() * 100, 1)}%")
kpi3.metric("Avg Height (in)", f"{round(filtered_df['AvgHeight'].mean(), 2)}")

# ---------------------------
# Chart Settings
# ---------------------------
color_options = ["Conference", "Playstyle_Cluster", "CoachChange"]
color_choice = st.selectbox("Color points by:", color_options)

numeric_options = [
    "win_pct", "OffEff", "DefEff", "O3PT_Share", "O2PT_Share", "OFT_Share", "D3PT_Share", "D2PT_Share", "DFT_Share",
    "avg_fga", "avg_fga3", "avg_fta", "avg_orb", "avg_drb", "avg_ast", "avg_to", "avg_stl", "avg_blk", "avg_pf",
    "avgBenchPoints"
]

def style_chart(fig, title, x_label=None, y_label=None):
    for trace in fig.data:
        if trace.type in ["scatter", "scattergl"]:
            trace.update(marker=dict(size=6))
    fig.update_layout(
        height=700,
        title=dict(text=title, font=dict(size=24)),
        margin=dict(l=200, r=50, t=80, b=50),
        showlegend=True,
        legend=dict(orientation="v", y=1, x=1.05),
        font=dict(size=16),
        xaxis_title=x_label,
        yaxis_title=y_label
    )
    return fig

# ---------------------------
# Scatter Plot 1: Tempo vs Game Stats
# ---------------------------
st.subheader("Tempo vs Game Stats")
y_axis_stat = st.selectbox("Choose Y-axis (Game Stat):", numeric_options)
fig1 = px.scatter(
    filtered_df, x="Tempo", y=y_axis_stat, color=color_choice,
    trendline="ols",
    color_discrete_map=color_map if color_choice == "Playstyle_Cluster" else None,
    hover_data=["Team", "win_pct", "OffEff", "DefEff", "avg_orb", "avg_ast"]
)
st.plotly_chart(style_chart(fig1, f"Tempo vs {y_axis_stat}", "Tempo", y_axis_stat), use_container_width=True)

# ---------------------------
# Scatter Plot 2: Roster Info vs Tempo
# ---------------------------
st.subheader("Roster Info vs Tempo")
roster_cols = ["AvgHeight", "avgCenterHeight", "avgPowerForwardHeight",
               "avgSmallForwardHeight", "avgShootingGuardHeight", "avgPointGuardHeight", "avgYearsOfExperience"]
x_axis_roster_tempo = st.selectbox("Choose X-axis (Roster Metric):", roster_cols, key="roster_tempo")
fig2 = px.scatter(
    filtered_df, x=x_axis_roster_tempo, y="Tempo", color=color_choice,
    trendline="ols",
    color_discrete_map=color_map if color_choice == "Playstyle_Cluster" else None,
    hover_data=["Team", "win_pct", "OffEff", "DefEff"]
)
st.plotly_chart(style_chart(fig2, f"{x_axis_roster_tempo} vs Tempo", x_axis_roster_tempo, "Tempo"), use_container_width=True)

# ---------------------------
# Scatter Plot 3: Roster Info vs Win%
# ---------------------------
st.subheader("Roster Info vs Win%")
x_axis_roster_win = st.selectbox("Choose X-axis (Roster Metric):", roster_cols, key="roster_win")
fig3 = px.scatter(
    filtered_df, x=x_axis_roster_win, y="win_pct", color=color_choice,
    trendline="ols",
    color_discrete_map=color_map if color_choice == "Playstyle_Cluster" else None,
    hover_data=["Team", "Tempo", "OffEff", "DefEff"]
)
st.plotly_chart(style_chart(fig3, f"{x_axis_roster_win} vs Win%", x_axis_roster_win, "Win%"), use_container_width=True)

# ---------------------------
# Cluster Composition Insights
# ---------------------------
st.subheader("Cluster Composition Insights")

# Tabs for five categories
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Point Share", "Shot Attempts", "Offensive Rebounds", "Defensive Rebounds", "Points by Position"
])

# Define color palettes for different charts
point_share_colors = ["#045a8d", "#238b45", "#fe9929"]  # Blue, Green, Orange for 3PT, 2PT, FT
shot_attempt_colors = ["#045a8d", "#238b45", "#fe9929"]  # Same logic for attempts
off_reb_colors = ["#54278f", "#756bb1", "#9e9ac8", "#bcbddc", "#dadaeb"]  # Purple gradient
def_reb_colors = ["#00441b", "#1b7837", "#5aae61", "#a6dba0", "#d9f0d3"]  # Green gradient
position_colors = ["#1f78b4", "#33a02c", "#e31a1c", "#ff7f00", "#6a3d9a"]  # Distinct colors for points by position

# Define columns for aggregation
point_share_cols = ["O3PT_Share", "O2PT_Share", "OFT_Share"]
shot_attempt_cols = ["avg_fga3", "avg_fga", "avg_fta"]
off_reb_cols = [
    "avgCenterOffensiveRebounds",
    "avgPowerForwardOffensiveRebounds",
    "avgSmallForwardOffensiveRebounds",
    "avgShootingGuardOffensiveRebounds",
    "avgPointGuardOffensiveRebounds"
]
def_reb_cols = [
    "avgCenterDefensiveRebounds",
    "avgPowerForwardDefensiveRebounds",
    "avgSmallForwardDefensiveRebounds",
    "avgShootingGuardDefensiveRebounds",
    "avgPointGuardDefensiveRebounds"
]
points_cols = [
    "avgCenterPoints",
    "avgPowerForwardPoints",
    "avgSmallForwardPoints",
    "avgShootingGuardPoints",
    "avgPointGuardPoints"
]

# Combine numeric columns for aggregation
numeric_cols = point_share_cols + shot_attempt_cols + off_reb_cols + def_reb_cols + points_cols

# Aggregate cluster data (only for active clusters)
cluster_group = filtered_clusters_df.groupby("Playstyle_Cluster")[numeric_cols].mean()

# ---------------------------
# TAB 1: Point Share
# ---------------------------
with tab1:
    st.markdown("### Point Share Breakdown by Playstyle Cluster")
    for cluster in active_clusters:
        if cluster in cluster_group.index:
            shares = cluster_group.loc[cluster, point_share_cols]
            fig_pie = px.pie(
                values=shares.values,
                names=["3PT", "2PT", "FT"],
                title=f"{cluster} - Point Share",
                color_discrete_sequence=point_share_colors
            )
            fig_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

# ---------------------------
# TAB 2: Shot Attempts
# ---------------------------
with tab2:
    st.markdown("### Shot Attempts Breakdown by Playstyle Cluster")
    for cluster in active_clusters:
        if cluster in cluster_group.index:
            attempts = cluster_group.loc[cluster, shot_attempt_cols]
            fig_attempts = px.pie(
                values=attempts.values,
                names=["3PT Attempts", "2PT Attempts", "FT Attempts"],
                title=f"{cluster} - Shot Attempts",
                color_discrete_sequence=shot_attempt_colors
            )
            fig_attempts.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_attempts, use_container_width=True)

# ---------------------------
# TAB 3: Offensive Rebounds
# ---------------------------
with tab3:
    st.markdown("### Offensive Rebounds by Position")
    for cluster in active_clusters:
        if cluster in cluster_group.index:
            rebounds = cluster_group.loc[cluster, off_reb_cols]
            fig_pie_off = px.pie(
                values=rebounds.values,
                names=["Center", "Power Forward", "Small Forward", "Shooting Guard", "Point Guard"],
                title=f"{cluster} - Offensive Rebounds",
                color_discrete_sequence=off_reb_colors
            )
            fig_pie_off.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie_off, use_container_width=True)

# ---------------------------
# TAB 4: Defensive Rebounds
# ---------------------------
with tab4:
    st.markdown("### Defensive Rebounds by Position")
    for cluster in active_clusters:
        if cluster in cluster_group.index:
            rebounds_def = cluster_group.loc[cluster, def_reb_cols]
            fig_pie_def = px.pie(
                values=rebounds_def.values,
                names=["Center", "Power Forward", "Small Forward", "Shooting Guard", "Point Guard"],
                title=f"{cluster} - Defensive Rebounds",
                color_discrete_sequence=def_reb_colors
            )
            fig_pie_def.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie_def, use_container_width=True)

# ---------------------------
# TAB 5: Points by Position
# ---------------------------
with tab5:
    st.markdown("### Average Points by Position (per Playstyle Cluster)")

    # Prepare data
    points_group = filtered_clusters_df.groupby("Playstyle_Cluster")[points_cols].mean().reset_index()
    points_melt = points_group.melt(id_vars="Playstyle_Cluster", value_vars=points_cols,
                                    var_name="Position", value_name="Average Points")

    # Rename positions for readability
    position_labels = {
        "avgCenterPoints": "Center",
        "avgPowerForwardPoints": "Power Forward",
        "avgSmallForwardPoints": "Small Forward",
        "avgShootingGuardPoints": "Shooting Guard",
        "avgPointGuardPoints": "Point Guard"
    }
    points_melt["Position"] = points_melt["Position"].map(position_labels)

    # Grouped bar chart (Position on X-axis, Points on Y-axis, color by cluster)
    fig_points = px.bar(
        points_melt,
        x="Position",
        y="Average Points",
        color="Playstyle_Cluster",
        barmode="group",
        title="Average Points by Position per Cluster",
        color_discrete_map=color_map  # Use consistent cluster colors
    )

    fig_points.update_layout(
        height=700,
        margin=dict(l=100, r=50, t=80, b=50),
        font=dict(size=16),
        xaxis_title="Position",
        yaxis_title="Average Points"
    )

    st.plotly_chart(fig_points, use_container_width=True)



# ---------------------------
# Positional Height Bar Chart
# ---------------------------
radar_height_features = st.sidebar.multiselect(
    "Height Metrics (for bar chart):",
    options=["avgPointGuardHeight", "avgShootingGuardHeight", "avgSmallForwardHeight", "avgPowerForwardHeight", "avgCenterHeight"],
    default=["avgPointGuardHeight", "avgShootingGuardHeight", "avgSmallForwardHeight", "avgPowerForwardHeight", "avgCenterHeight"]
)

if radar_height_features:
    cluster_means_height = filtered_clusters_df.groupby("Playstyle_Cluster")[radar_height_features].mean().reset_index()

    # Melt for bar chart
    height_melt = cluster_means_height.melt(id_vars="Playstyle_Cluster", value_vars=radar_height_features,
                                            var_name="Position", value_name="Average Height")

    # Rename x-axis positions for readability
    position_labels = {
        "avgPointGuardHeight": "Point Guard",
        "avgShootingGuardHeight": "Shooting Guard",
        "avgSmallForwardHeight": "Small Forward",
        "avgPowerForwardHeight": "Power Forward",
        "avgCenterHeight": "Center"
    }
    height_melt["Position"] = height_melt["Position"].map(position_labels)

    fig_height_bar = px.bar(
        height_melt,
        x="Position",
        y="Average Height",
        color="Playstyle_Cluster",
        color_discrete_map=color_map,
        barmode="group",
        title="Average Positional Heights by Playstyle Cluster"
    )

    fig_height_bar.update_xaxes(showgrid=False)
    for i in range(1, len(position_labels)):
        fig_height_bar.add_vline(
            x=i - 0.5,
            line_width=1,
            line_dash="dash",
            line_color="lightgray"
        )

    fig_height_bar.update_layout(
        height=700,
        margin=dict(l=100, r=50, t=80, b=50),
        font=dict(size=16),
        yaxis_title="Average Height (inches)"
    )

    st.plotly_chart(fig_height_bar, use_container_width=True, key="height_bar")
