import streamlit as st
from streamlit import title

# Define the pages
raw_data = st.Page("raw_data.py", title="Raw data", icon="🎈")
year_state = st.Page("year_state.py", title="Year & State summary", icon="🗓️")
state_year = st.Page("state_year.py", title="State & Year summary", icon="🏛️")

# Set up navigation
pg = st.navigation([raw_data, year_state, state_year])
pg.run()