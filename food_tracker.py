import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px  # For perfect bars
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

# Initialize the database (persists on Streamlit Cloud)
@st.cache_resource
def init_db():
    conn = sqlite3.connect('food_expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            meal TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Food Tracker", page_icon="🍽️", layout="wide")  # Mobile-optimized layout

# Fun, colorful header
st.markdown("""
    <style>
    .main-header {color: #FF6B6B; font-size: 3rem; text-align: center; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)
st.markdown('<h1 class="main-header">🍽️ Food Expenses Tracker</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar for navigation (collapses nicely on mobile)
with st.sidebar:
    st.title("🚀 Navigation")
    page = st.selectbox("Choose a page", ["Daily Entry", "Monthly Summary", "Debug DB"])

if page == "Daily Entry":
    # Date selection (compact for mobile)
    selected_date = st.date_input("📅 Select Date", value=date.today(), key="date_mobile")
    
    # Function to get existing amount for a meal (handles Other with desc, backward compat for old names)
    def get_existing_amount(meal_name):
        conn = sqlite3.connect('food_expenses.db')
        if meal_name == "Other":
            query = "SELECT amount FROM expenses WHERE date = ? AND (meal LIKE 'Other%' OR meal = 'Other') ORDER BY id DESC LIMIT 1"
            df = pd.read_sql_query(query, conn, params=(selected_date,))
        else:
            # Backward compat: Check old names too (e.g., 'Morning' -> 'Breakfast')
            old_names = {'Morning': 'Breakfast', 'Afternoon': 'Lunch', 'Evening': 'Dinner'}
            query = "SELECT amount FROM expenses WHERE date = ? AND meal = ?"
            df = pd.read_sql_query(query, conn, params=(selected_date, meal_name))
            if df.empty and meal_name in old_names:
                df = pd.read_sql_query(query, conn, params=(selected_date, old_names[meal_name]))
        conn.close()
        return df['amount'].iloc[0] if not df.empty else None
    
    # Function to delete entry for a meal (handles Other with desc, backward compat)
    def delete_entry(meal_name):
        conn = sqlite3.connect('food_expenses.db')
        if meal_name == "Other":
            conn.execute("DELETE FROM expenses WHERE date = ? AND (meal LIKE 'Other%' OR meal = 'Other')", (selected_date,))
        else:
            old_names = {'Morning': 'Breakfast', 'Afternoon': 'Lunch', 'Evening': 'Dinner'}
            if meal_name in old_names:
                meal_name = old_names[meal_name]
            conn.execute("DELETE FROM expenses WHERE date = ? AND meal = ?", (selected_date, meal_name))
        conn.commit()
        conn.close()
        st.rerun()
    
    # Function to save or update entry (uses new names)
    def save_entry(meal_name, amount, desc=""):
        conn = sqlite3.connect('food_expenses.db')
        # Delete if exists (new or old name)
        if meal_name == "Other":
            conn.execute("DELETE FROM expenses WHERE date = ? AND (meal LIKE 'Other%' OR meal = 'Other')", (selected_date,))
        else:
            old_names = {'Breakfast': 'Morning', 'Lunch': 'Afternoon', 'Dinner': 'Evening'}
            if meal_name in old_names.values():
                for k, v in old_names.items():
                    if v == meal_name:
                        meal_name = k
                        break
            conn.execute("DELETE FROM expenses WHERE date = ? AND meal = ?", (selected_date, meal_name))
        if amount > 0:
            full_meal = f"{meal_name}: {desc}" if desc and meal_name == "Other" else meal_name
            conn.execute(
                "INSERT INTO expenses (date, meal, amount) VALUES (?, ?, ?)",
                (selected_date, full_meal, amount)
            )
        conn.commit()
        conn.close()
        st.rerun()
    
    # Mobile-friendly inputs with delete logic (New names: Breakfast, Lunch, Dinner, Other)
    st.subheader("💰 Enter Amounts (₹)")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🍳 Breakfast")
        breakfast_amt = get_existing_amount("Breakfast")
        if breakfast_amt is not None:
            col_m, col_del_m = st.columns([3, 1])
            with col_m:
                st.info(f"₹{breakfast_amt:.2f}")
            with col_del_m:
                if st.button("🗑️ Delete", key="del_breakfast"):
                    delete_entry("Breakfast")
        else:
            breakfast_input = st.text_input("", placeholder="e.g., 50.00", key="breakfast_mobile")
            try:
                parsed_breakfast = float(breakfast_input) if breakfast_input.strip() != "" else 0.0
            except ValueError:
                parsed_breakfast = 0.0
                if breakfast_input.strip() != "":
                    st.error("Enter a valid number (e.g., 50.00)")
            if st.button("💾 Save Breakfast", key="save_breakfast"):
                save_entry("Breakfast", parsed_breakfast)
    
    with col2:
        st.markdown("### 🥗 Lunch")
        lunch_amt = get_existing_amount("Lunch")
        if lunch_amt is not None:
            col_a, col_del_a = st.columns([3, 1])
            with col_a:
                st.info(f"₹{lunch_amt:.2f}")
            with col_del_a:
                if st.button("🗑️ Delete", key="del_lunch"):
                    delete_entry("Lunch")
        else:
            lunch_input = st.text_input("", placeholder="e.g., 80.00", key="lunch_mobile")
            try:
                parsed_lunch = float(lunch_input) if lunch_input.strip() != "" else 0.0
            except ValueError:
                parsed_lunch = 0.0
                if lunch_input.strip() != "":
                    st.error("Enter a valid number (e.g., 80.00)")
            if st.button("💾 Save Lunch", key="save_lunch"):
                save_entry("Lunch", parsed_lunch)
    
    # Dinner and Other in next row for better mobile stack
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### 🍽️ Dinner")
        dinner_amt = get_existing_amount("Dinner")
        if dinner_amt is not None:
            col_e, col_del_e = st.columns([3, 1])
            with col_e:
                st.info(f"₹{dinner_amt:.2f}")
            with col_del_e:
                if st.button("🗑️ Delete", key="del_dinner"):
                    delete_entry("Dinner")
        else:
            dinner_input = st.text_input("", placeholder="e.g., 60.00", key="dinner_mobile")
            try:
                parsed_dinner = float(dinner_input) if dinner_input.strip() != "" else 0.0
            except ValueError:
                parsed_dinner = 0.0
                if dinner_input.strip() != "":
                    st.error("Enter a valid number (e.g., 60.00)")
            if st.button("💾 Save Dinner", key="save_dinner"):
                save_entry("Dinner", parsed_dinner)
    
    with col4:
        st.markdown("### 🍟 Other")
        other_amt = get_existing_amount("Other")
        if other_amt is not None:
            col_o, col_del_o = st.columns([3, 1])
            with col_o:
                st.info(f"₹{other_amt:.2f}")
            with col_del_o:
                if st.button("🗑️ Delete", key="del_other"):
                    delete_entry("Other")
        else:
            other_input = st.text_input("", placeholder="e.g., 20.00", key="other_mobile")
            other_desc = st.text_input("Quick note (e.g., 'snack')", max_chars=20, key="desc_mobile")
            try:
                parsed_other = float(other_input) if other_input.strip() != "" else 0.0
            except ValueError:
                parsed_other = 0.0
                if other_input.strip() != "":
                    st.error("Enter a valid number (e.g., 20.00)")
            if st.button("💾 Save Other", key="save_other"):
                save_entry("Other", parsed_other, other_desc)
    
    # Clear All Button
    if st.button("🗑️ Clear All Today's Entries", type="secondary"):
        conn = sqlite3.connect('food_expenses.db')
        conn.execute("DELETE FROM expenses WHERE date = ?", (selected_date,))
        conn.commit()
        conn.close()
        st.success("All cleared! Start fresh. 🔄")
        st.rerun()
    
    # Get daily total from DB
    conn = sqlite3.connect('food_expenses.db')
    df_today = pd.read_sql_query(
        "SELECT amount FROM expenses WHERE date = ?",
        conn, params=(selected_date,)
    )
    conn.close()
    daily_total = df_today['amount'].sum() if not df_today.empty else 0.0
    st.markdown(f"### **Daily Total: ₹{daily_total:.2f}**")
    
    # Responsive feedback based on total
    if daily_total > 220:
        st.error("🚨 Whoa! Over ₹220—time to skip dessert? Watch those extras!")
    elif daily_total < 150:
        st.success("🎉 Congrats! Under ₹150—you saved today! Treat yourself wisely!")
    else:
        st.info("👍 On track (₹150-220)—keep it steady! 💪")
    
    # View all today's entries (compact table)
    st.subheader("📋 Today's Entries")
    conn = sqlite3.connect('food_expenses.db')
    df_entries = pd.read_sql_query(
        "SELECT meal, amount FROM expenses WHERE date = ? ORDER BY meal",
        conn, params=(selected_date,)
    )
    conn.close()
    if not df_entries.empty:
        df_entries['amount'] = df_entries['amount'].apply(lambda x: f"₹{x:.2f}")
        st.dataframe(df_entries, use_container_width=True)
    else:
        st.info("No entries yet—add some! 🌟")

elif page == "Monthly Summary":
    # Month selection (clearer label)
    today = date.today()
    selected_month = st.date_input("Select Month (pick 1st for full view!)", value=today.replace(day=1), key="month_mobile")
    
    # Calculate month range
    month_start = selected_month.replace(day=1)  # Ensure it's 1st
    next_month = month_start + relativedelta(months=1)
    month_end = next_month - timedelta(days=1)
    
    # Fetch data
    conn = sqlite3.connect('food_expenses.db')
    df_month = pd.read_sql_query(
        "SELECT date, meal, amount FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date",
        conn, params=(month_start, month_end)
    )
    conn.close()
    
    if not df_month.empty:
        st.subheader(f"📊 Summary: {month_start.strftime('%B %Y')} 🌟")
        
        # Daily totals (raw for calc, styled for display)
        df_month['date'] = pd.to_datetime(df_month['date'])
        daily_totals_raw = df_month.groupby('date')['amount'].sum().reset_index()
        daily_totals_raw['date'] = daily_totals_raw['date'].dt.strftime('%Y-%m-%d')
        daily_totals_raw.columns = ['Date', 'Total']
        daily_totals_styled = daily_totals_raw.style.format({'Total': '₹{:.2f}'})
        st.subheader("Daily Breakdown 📈")
        st.dataframe(daily_totals_styled, use_container_width=True)
        
        # Monthly total
        monthly_total = df_month['amount'].sum()
        st.markdown(f"### **Monthly Total: ₹{monthly_total:.2f}** 🎯")
        
        # Meal breakdown (group all variants into 4 categories: Breakfast, Lunch, Dinner, Other)
        def categorize_meal(meal):
            meal_lower = str(meal).lower()
            if any(word in meal_lower for word in ['breakfast', 'morning']):
                return 'Breakfast'
            elif any(word in meal_lower for word in ['lunch', 'afternoon']):
                return 'Lunch'
            elif any(word in meal_lower for word in ['dinner', 'evening']):
                return 'Dinner'
            else:
                return 'Other'
        
        df_month['meal_group'] = df_month['meal'].apply(categorize_meal)
        meal_breakdown_raw_grouped = df_month.groupby('meal_group')['amount'].sum().reset_index()
        meal_breakdown_raw_grouped.columns = ['Meal', 'Total']
        # Sort by total descending for better view
        meal_breakdown_raw_grouped = meal_breakdown_raw_grouped.sort_values('Total', ascending=False).reset_index(drop=True)
        meal_breakdown_styled = meal_breakdown_raw_grouped.style.format({'Total': '₹{:.2f}'})
        st.subheader("By Meal Type 🥗")
        st.dataframe(meal_breakdown_styled, use_container_width=True)
        
        # Perfect bars with Plotly (use grouped raw DF)
        fig = px.bar(meal_breakdown_raw_grouped, x='Meal', y='Total', title="Meal Breakdown",
                     color='Meal', color_discrete_sequence=px.colors.qualitative.Set3,
                     height=300,  # Balanced height
                     hover_data={'Total': ':.2f'})  # Hover shows ₹ via custom text if needed
        fig.update_traces(hovertemplate='<b>%{x}</b><br>₹%{y:.2f}<extra></extra>')  # Custom hover with ₹
        fig.update_layout(xaxis_title="Meal", yaxis_title="Amount (₹)", showlegend=False)
        fig.update_traces(marker_line_color='white', marker_line_width=1)  # Clean borders
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet—start entering daily! Or pick the right month's 1st day (e.g., 2025-09-01). 🚀")
    
    # Reset button in sidebar
    if st.sidebar.button("🗑️ Clear All Data (Careful!)"):
        conn = sqlite3.connect('food_expenses.db')
        conn.execute("DELETE FROM expenses")
        conn.commit()
        conn.close()
        st.sidebar.success("Cleared! 🔄")
        st.rerun()

elif page == "Debug DB":
    st.subheader("🔍 All Entries in DB (Newest First)")
    conn = sqlite3.connect('food_expenses.db')
    df_all = pd.read_sql_query(
        "SELECT id, date, meal, amount FROM expenses ORDER BY date DESC, id DESC",
        conn
    )
    conn.close()
    if not df_all.empty:
        df_all['amount'] = df_all['amount'].apply(lambda x: f"₹{x:.2f}")
        st.dataframe(df_all, use_container_width=True)
        st.info("💡 Look for September dates here. If missing, re-enter on this app (cloud/local match matters!).")
    else:
        st.warning("DB empty—no entries saved yet. Add some in Daily Entry!")
    
    # Quick filter for September
    if st.checkbox("Filter to September Only"):
        conn = sqlite3.connect('food_expenses.db')
        df_sept = pd.read_sql_query(
            "SELECT id, date, meal, amount FROM expenses WHERE date LIKE '2025-09%' ORDER BY date DESC, id DESC",
            conn
        )
        conn.close()
        if not df_sept.empty:
            df_sept['amount'] = df_sept['amount'].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(df_sept, use_container_width=True)
            st.success(f"September has {len(df_sept)} entries. Total: ₹{df_sept['amount'].str.replace('₹', '').str.replace(',', '').astype(float).sum():.2f}")
        else:
            st.info("No September data—try entering a test entry for 2025-09-01.")

st.markdown("---")
st.caption("💡 Updated: Clean categories (Breakfast/Lunch/Dinner/Other) + Debug page to check saves. Select exact month start! 🌈")