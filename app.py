import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# Constants
DATA_FILE = "focus_data.csv"

# Initialize CSV if not exists
def init_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["timestamp", "study_time", "distractions", "focus_score", "reward_time"])
        df.to_csv(DATA_FILE, index=False)

def load_data():
    return pd.read_csv(DATA_FILE)

def save_session(study_time, distractions, focus_score, reward_time):
    df = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "study_time": study_time,
        "distractions": distractions,
        "focus_score": focus_score,
        "reward_time": reward_time
    }])
    df.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)

def get_best_study_time(df):
    if df.empty:
        return None
    
    temp_df = df.copy()
    temp_df['hour'] = pd.to_datetime(temp_df['timestamp']).dt.hour
    hourly_avg = temp_df.groupby('hour')['focus_score'].mean()
    
    if hourly_avg.empty:
        return None
        
    best_hour = hourly_avg.idxmax()
    
    am_pm = "AM" if best_hour < 12 else "PM"
    display_hour = best_hour if best_hour <= 12 else best_hour - 12
    if display_hour == 0:
        display_hour = 12
        
    return f"{display_hour}:00 {am_pm}"

def get_top_study_hours(df):
    if df.empty:
        return []
    
    temp_df = df.copy()
    temp_df['hour'] = pd.to_datetime(temp_df['timestamp']).dt.hour
    hourly_avg = temp_df.groupby('hour')['focus_score'].mean().sort_values(ascending=False)
    
    top_hours = []
    for hour, score in hourly_avg.head(3).items():
        am_pm = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        top_hours.append(f"{display_hour}:00 {am_pm} (Avg Score: {score:.1f})")
    
    return top_hours

def main():
    st.set_page_config(page_title="DeepFocus", page_icon="🎯", layout="wide")
    init_data()
    
    # Initialize session state variables
    if 'distractions' not in st.session_state:
        st.session_state.distractions = 0
    
    # Sidebar Navigation
    st.sidebar.title("🎯 DeepFocus")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Start Session", "Analytics", "AI Coach"])
    
    df = load_data()
    
    if page == "Dashboard":
        st.title("📊 Dashboard")
        
        if df.empty:
            st.info("No data yet. Start a session to see your dashboard!")
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            total_study_time = df['study_time'].sum()
            avg_focus_score = df['focus_score'].mean()
            total_rewards = df['reward_time'].sum()
            best_time = get_best_study_time(df)
            
            col1.metric("Total Study Time (min)", f"{total_study_time:.0f}")
            col2.metric("Avg Focus Score", f"{avg_focus_score:.1f}")
            col3.metric("Total Rewards (min)", f"{total_rewards:.1f}")
            col4.metric("Best Study Time", best_time if best_time else "N/A")
            
            st.subheader("Focus Trend")
            st.line_chart(df.set_index('timestamp')['focus_score'])
            
            # Smart Pomodoro System
            st.subheader("🍅 Smart Pomodoro Suggestion")
            if avg_focus_score > 25:
                st.success("Your focus is excellent! Suggested Pomodoro: 40 minutes.")
            elif avg_focus_score < 15:
                st.warning("You might be struggling to focus. Suggested Pomodoro: 15 minutes.")
            else:
                st.info("Suggested Pomodoro: 25 minutes.")

    elif page == "Start Session":
        st.title("⏱️ Start Focus Session")
        
        # Timer State Initialization
        if 'timer_running' not in st.session_state:
            st.session_state.timer_running = False
        if 'remaining_time' not in st.session_state:
            st.session_state.remaining_time = 25 * 60
        if 'elapsed_seconds' not in st.session_state:
            st.session_state.elapsed_seconds = 0
        if 'last_update' not in st.session_state:
            st.session_state.last_update = time.time()

        study_time_minutes = st.slider("Select Study Time (minutes)", 15, 60, 25)
        
        # Only reset if the timer is NOT running AND the user changed the slider
        if not st.session_state.timer_running:
            if 'prev_slider' not in st.session_state or st.session_state.prev_slider != study_time_minutes:
                st.session_state.remaining_time = study_time_minutes * 60
                st.session_state.elapsed_seconds = 0
                st.session_state.prev_slider = study_time_minutes

        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("▶️ Start Timer", use_container_width=True, disabled=st.session_state.timer_running):
                st.session_state.timer_running = True
                st.session_state.last_update = time.time()
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop Timer", use_container_width=True, disabled=not st.session_state.timer_running):
                st.session_state.timer_running = False
                st.rerun()

        # Timer Display
        timer_placeholder = st.empty()
        
        while st.session_state.timer_running and st.session_state.remaining_time > 0:
            now = time.time()
            elapsed = now - st.session_state.last_update
            if elapsed >= 1:
                seconds_to_add = int(elapsed)
                st.session_state.remaining_time -= seconds_to_add
                st.session_state.elapsed_seconds += seconds_to_add
                st.session_state.last_update = now
            
            mins, secs = divmod(max(st.session_state.remaining_time, 0), 60)
            timer_placeholder.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
            
            if st.session_state.remaining_time <= 0:
                st.session_state.timer_running = False
                st.balloons()
                st.success("Time's up! Great job staying focused.")
                break
                
            time.sleep(0.1) 
            st.rerun() 

        # Static display if not running
        if not st.session_state.timer_running:
            mins, secs = divmod(max(st.session_state.remaining_time, 0), 60)
            timer_placeholder.metric("Time Remaining", f"{mins:02d}:{secs:02d}")

        st.divider()
        
        # Automatic Distraction Detection (JS Injection)
        if st.session_state.timer_running:
            st.components.v1.html("""
                <script>
                    const parentDoc = window.parent.document;
                    if (!window.parent.distractionListenerAdded) {
                        parentDoc.addEventListener("visibilitychange", () => {
                            if (parentDoc.visibilityState === "hidden") {
                                const buttons = Array.from(parentDoc.querySelectorAll("button"));
                                const trigger = buttons.find(btn => btn.innerText.includes("REPORT_DISTRACTION"));
                                if (trigger) trigger.click();
                            }
                        });
                        window.parent.distractionListenerAdded = true;
                    }
                </script>
            """, height=0)

        # Hidden button for JS to trigger distraction increment
        st.markdown("""
            <style>
            /* Hide the distraction report button */
            div[data-testid="stButton"] button:contains("REPORT_DISTRACTION") {
                display: none !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        if st.button("REPORT_DISTRACTION", key="distraction_report_btn"):
            if st.session_state.timer_running:
                st.session_state.distractions += 1
                st.rerun()

        distractions = st.number_input("Number of Distractions", min_value=0, value=st.session_state.distractions, key="distraction_input")
        # Sync manual input back to session state
        st.session_state.distractions = distractions
        
        if st.button("End Session & Save"):
            # Calculate actual time spent based on elapsed seconds
            actual_time_spent = st.session_state.elapsed_seconds / 60
            
            # Use the distractions from session state
            current_distractions = st.session_state.distractions
            
            # Minimum 0.1 min for logging to avoid division by zero or empty sessions
            if actual_time_spent < 0.1:
                st.warning("Session too short to log. Please run the timer for at least a few seconds.")
            else:
                focus_score = actual_time_spent - (current_distractions * 2)
                reward_time = 0.25 * actual_time_spent
                
                save_session(actual_time_spent, current_distractions, focus_score, reward_time)
                
                st.success("Session saved successfully!")
                
                # Display results
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Study Time", f"{actual_time_spent:.2f} min")
                res_col2.metric("Distractions", current_distractions)
                res_col3.metric("Focus Score", f"{focus_score:.2f}")
                
                st.info(f"🎁 Reward Earned: {reward_time:.2f} minutes")
                
                # Reset timer and distractions for next session
                st.session_state.remaining_time = study_time_minutes * 60
                st.session_state.elapsed_seconds = 0
                st.session_state.distractions = 0
                st.session_state.timer_running = False
                st.rerun()

        st.divider()
        st.subheader("Multi-Level Distraction Control")
        
        if 'social_clicks' not in st.session_state:
            st.session_state.social_clicks = 0
            
        if st.session_state.social_clicks < 3:
            if st.button("Open Social Media"):
                st.session_state.social_clicks += 1
                
                if st.session_state.social_clicks == 1:
                    st.warning("⚠️ Are you sure? This will break your focus!")
                elif st.session_state.social_clicks == 2:
                    with st.spinner("Delaying access to help you reconsider..."):
                        time.sleep(3)
                    st.error("Accessing social media...")
        else:
            st.button("Open Social Media", disabled=True)
            st.error("🛑 Button disabled. Focus on your work!")

    elif page == "Analytics":
        st.title("📈 Analytics")
        
        if df.empty:
            st.info("Complete some sessions to see performance tracking.")
        else:
            # Performance Tracking
            if len(df) >= 2:
                latest = df.iloc[-1]
                previous = df.iloc[-2]
                improvement = ((latest['focus_score'] - previous['focus_score']) / previous['focus_score']) * 100 if previous['focus_score'] > 0 else 0
                
                st.subheader("Performance Tracking")
                col1, col2 = st.columns(2)
                col1.metric("Latest Focus Score", f"{latest['focus_score']:.1f}", f"{improvement:.1f}% vs previous")
                col2.metric("Previous Focus Score", f"{previous['focus_score']:.1f}")
            
            st.divider()
            
            # Time of Day Analysis
            st.subheader("🕒 Focus by Time of Day")
            temp_df = df.copy()
            temp_df['hour'] = pd.to_datetime(temp_df['timestamp']).dt.hour
            hourly_data = temp_df.groupby('hour')['focus_score'].mean().reset_index()
            
            # Create a full 24h range for the chart
            all_hours = pd.DataFrame({'hour': range(24)})
            hourly_data = pd.merge(all_hours, hourly_data, on='hour', how='left').fillna(0)
            
            st.bar_chart(hourly_data.set_index('hour'))
            
            # Best Hours Suggestions
            top_hours = get_top_study_hours(df)
            if top_hours:
                st.success("🌟 **Your Best Hours to Study:**")
                for i, h in enumerate(top_hours):
                    st.write(f"{i+1}. {h}")
            
            st.divider()
            st.subheader("Session History")
            st.dataframe(df.tail(10))

    elif page == "AI Coach":
        st.title("🤖 AI Study Coach")
        
        if df.empty:
            st.info("💡 Suggestion: Start a focus session to get personalized advice.")
        else:
            latest_score = df.iloc[-1]['focus_score']
            best_time = get_best_study_time(df)
            
            st.subheader("Personalized Advice")
            
            if best_time:
                st.success(f"📅 **Time Optimization:** Your data shows you are most productive around **{best_time}**. Try to schedule your most challenging tasks during this window!")
            
            if latest_score < 15:
                st.warning("💡 **Focus Tip:** Try to reduce distractions in your next session. Consider putting your phone in another room.")
            elif latest_score >= 25:
                st.success("💡 **Encouragement:** Great work! You are maintaining excellent focus. Keep it up!")
            else:
                st.info("💡 **Growth Tip:** You're doing well. Try to push for a slightly longer session next time to enter deep work.")
            
            # General Tips
            with st.expander("More Study Tips"):
                st.write("- **Environment:** Keep your desk clean to reduce visual distractions.")
                st.write("- **Hydration:** Drink water regularly to maintain cognitive function.")
                st.write("- **Breaks:** Use the reward time you earn to take a real break (no screens!).")

if __name__ == "__main__":
    main()
