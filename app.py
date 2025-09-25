import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from supabase import create_client

st.title("🏆 Ballon d'Or 2025 Top Players")

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check if environment variables are loaded
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Missing Supabase credentials. Please check your .env file.")
    st.stop()


try:
    # Create Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch data with correct order syntax
    data = supabase.table("ballon_dor_players").select("*").order("ranking").execute()
    df = pd.DataFrame(data.data)
    
    
    if df.empty:
        st.warning("⚠️ No data found. The 'ballon_dor_players' table is empty or doesn't exist.")
        st.info("💡 Run the collector_uploader.py script first to populate the database.")
    else:
        # Add some styling and header
        st.markdown("---")
        st.markdown("### 🥇 The Golden Ball Winner")
        
        # Highlight the winner
        winner = df[df["ranking"] == 1].iloc[0]
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #FFD700, #FFA500); border-radius: 10px; margin: 10px 0;">
                <h2 style="color: white; margin: 0;">🏆 {winner['name']} 🏆</h2>
                <h3 style="color: white; margin: 5px 0;">{winner['club']}</h3>
                <p style="color: white; margin: 0;">Ballon d'Or 2025 Winner</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Top 3 Podium
        st.markdown("### 🏅 Podium - Top 3")
        top3 = df.head(3)
        
        col1, col2, col3 = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
        
        for i, (_, player) in enumerate(top3.iterrows()):
            with [col1, col2, col3][i]:
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: {colors[i]}; border-radius: 10px; margin: 5px 0;">
                    <h3 style="color: white; margin: 0;">{medals[i]} #{player['ranking']}</h3>
                    <h4 style="color: white; margin: 5px 0;">{player['name']}</h4>
                    <p style="color: white; margin: 0;">{player['club']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Statistics
        st.markdown("### 📊 Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Players", len(df))
        with col2:
            top_club = df["club"].mode().iloc[0]
            club_count = df["club"].value_counts().iloc[0]
            st.metric("Most Represented Club", f"{top_club} ({club_count})")
        with col3:
            st.metric("Winner", winner['name'])
        with col4:
            avg_ranking = df["ranking"].mean()
            st.metric("Average Ranking", f"{avg_ranking:.1f}")
        
        # Club Distribution Chart
        st.markdown("### 🏟️ Club Representation")
        club_counts = df["club"].value_counts()
        
        fig_clubs = px.pie(
            values=club_counts.values, 
            names=club_counts.index,
            title="Players by Club",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_clubs.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_clubs, width='stretch')
        
        # Full Rankings Table (without ID and row numbers)
        st.markdown("### 📋 Complete Rankings")
        
        # Create a styled dataframe without ID and row numbers
        display_df = df[["ranking", "name", "club"]].copy()
        display_df.columns = ["Rank", "Player Name", "Club"]
        
        # Add some styling
        def highlight_top3(row):
            if row["Rank"] <= 3:
                return ['background-color: #FFD700' if row["Rank"] == 1 
                       else 'background-color: #C0C0C0' if row["Rank"] == 2
                       else 'background-color: #CD7F32' for _ in row]
            return [''] * len(row)
        
        styled_df = display_df.style.apply(highlight_top3, axis=1)
        st.dataframe(styled_df, width='stretch', hide_index=True)

except Exception as e:
    st.error(f"❌ Database error: {str(e)}")
    st.info("💡 Make sure the 'ballon_dor_players' table exists in your Supabase database.")
