import requests
from datetime import datetime, UTC
import pandas as pd
import streamlit as st

API_KEY = "pk_36511269_YQEXQ4Q6DD9ED827T9TEZ27MV5S6SVFV"
SPACE_ID = "42540422"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}

@st.cache_data
def fetch_all_folder_names():
    excluded_folders = ["WIP", "ARHIVA", "INFO", "R&D", "admin"]
    folders = []
    for archived in [False, True]:
        url = f"https://api.clickup.com/api/v2/space/{SPACE_ID}/folder?archived={str(archived).lower()}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            folders.extend(response.json().get("folders", []))
    return sorted([f["name"] for f in folders if f["name"] not in excluded_folders])

def get_folders(selected_folder_name):
    folders = []
    for archived in [False, True]:
        url = f"https://api.clickup.com/api/v2/space/{SPACE_ID}/folder?archived={str(archived).lower()}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            folders.extend(response.json().get("folders", []))
    return [f for f in folders if f.get("name") == selected_folder_name]

def get_lists(folder_id):
    lists = []
    for archived in [False, True]:
        url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list?archived={str(archived).lower()}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            lists.extend(response.json().get("lists", []))
    return lists

def get_tasks(list_id):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("tasks", [])
    return []

def convert_timestamp_to_date(timestamp):
    if timestamp:
        return datetime.fromtimestamp(int(timestamp) / 1000, UTC).strftime('%Y-%m-%d')
    return ""

@st.cache_data
def load_clickup_data(folder_name):
    folders = get_folders(folder_name)
    all_lists = []
    all_tasks_data = []
    for folder in folders:
        lists = get_lists(folder["id"])
        all_lists.extend(lists)
        for lista in lists:
            list_name = lista["name"]
            tasks = get_tasks(lista["id"])
            for task in tasks:
                all_tasks_data.append({
                    "task_id": task["id"],
                    "task_name": task["name"],
                    "date_done": convert_timestamp_to_date(task.get("date_done", "")),
                    "assignees": ", ".join([a["username"] for a in task.get("assignees", [])]),
                    "points": int(task.get("points", 0) or 0),
                    "list_name": list_name,
                    "folder_name": folder["name"]
                })
    return pd.DataFrame(all_tasks_data), sorted({l["name"] for l in all_lists})

def build_pivot(df, value_field):
    expanded_rows = []
    for _, row in df.iterrows():
        assignees = [name.strip() for name in row["assignees"].split(",") if name.strip()]
        value = row[value_field] if value_field == "points" else 1
        value_per_user = value / len(assignees) if assignees else 0
        for user in assignees:
            expanded_rows.append({
                "list_name": row["list_name"],
                "user": user,
                value_field: value_per_user
            })
    expanded_df = pd.DataFrame(expanded_rows)
    pivot_df = expanded_df.pivot_table(index="list_name", columns="user", values=value_field, aggfunc="sum", fill_value=0)
    pivot_df["Total"] = pivot_df.sum(axis=1)
    num_users = (pivot_df.drop(columns="Total") > 0).sum(axis=1)
    pivot_df["Medie"] = pivot_df["Total"] / num_users
    user_cols = [c for c in pivot_df.columns if c not in ["Total", "Medie"]]
    pivot_df["Mediana"] = pivot_df[user_cols].median(axis=1)
    return pivot_df.round(2)

def style_pivot_table(pivot_df):
    def style_func(val, median):
        try:
            return 'color: red' if pd.notna(val) and val < float(median) else ''
        except:
            return ''
    if "Mediana" not in pivot_df.columns:
        return pivot_df.round(2)  # fără stilizare dacă nu avem Mediana
    return pivot_df.round(2).style.apply(
        lambda row: [style_func(val, row["Mediana"]) for val in row],
        axis=1
    )

# --- Streamlit App ---
st.set_page_config("Raport Sprinturi", layout="wide")
st.title("Raport Sprinturi")

folder_names = fetch_all_folder_names()
default_folder = "2025 Q1"
selected_folder = st.selectbox("Selectează perioada:", folder_names, index=folder_names.index(default_folder) if default_folder in folder_names else 0)

df, all_lists = load_clickup_data(selected_folder)

if "reincarca" not in st.session_state:
    st.session_state.reincarca = False

selected_lists = st.multiselect("Selectează sprinturile:", options=all_lists, default=all_lists, key="lists")
user_columns = [col for col in df["assignees"].str.split(", ").explode().unique() if col]

selected_users = st.multiselect("Alege oamenii:", options=user_columns, default=user_columns, key="users")

col1, col2, col3 = st.columns(3)
show_total = col1.toggle("afișează Total", value=True, key="total")
show_medie = col2.toggle("afișează Medie", value=False, key="medie")
show_mediana = col3.toggle("afișează Mediana", value=False, key="mediana")

if st.button("Afișează / Reîncarcă"):
    st.session_state.reincarca = True

if st.session_state.reincarca:
    filtered_df = df[df["list_name"].isin(st.session_state.lists)]
    pivot_points = build_pivot(filtered_df, "points")
    pivot_tasks = build_pivot(filtered_df, "task_id")

    columns_to_show = st.session_state.users.copy()
    if st.session_state.total: columns_to_show.append("Total")
    if st.session_state.medie: columns_to_show.append("Medie")
    if st.session_state.mediana: columns_to_show.append("Mediana")

    st.subheader("Puncte / utilizator / sprint")
    st.line_chart(pivot_points[columns_to_show], height=500)
    with st.expander("🔍 Vezi tabelul cu puncte"):
        st.dataframe(style_pivot_table(pivot_points[columns_to_show]))

    st.subheader("Număr de taskuri / utilizator / sprint")
    st.line_chart(pivot_tasks[columns_to_show], height=500)
    with st.expander("🔍 Vezi tabelul cu taskuri"):
        st.dataframe(style_pivot_table(pivot_tasks[columns_to_show]))