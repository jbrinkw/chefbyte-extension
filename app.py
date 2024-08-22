import streamlit as st
from openai import OpenAI
import pandas as pd
import psycopg2
import json
from datetime import datetime

# Set up the Streamlit page configuration
st.set_page_config(page_title="ChefByte", page_icon="🍳")
st.title("🍳 ChefByte")

# Initialize the OpenAI client
openai_api_key = ''
client = OpenAI(api_key=openai_api_key)

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname="mydatabase",
        user="myuser",
        password="mypassword",
        host="localhost",
        port="5432"
    )

# Create necessary database tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create inventory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            quantity INTEGER NOT NULL,
            expiration DATE
        )
    """)
    # Create taste profile table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS taste_profile (
            id SERIAL PRIMARY KEY,
            profile TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# Update or add an item to the inventory
def update_item_in_inventory(name, quantity, expiration):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if the item already exists
    cur.execute("SELECT id, quantity FROM inventory WHERE name = %s AND expiration = %s", (name, expiration))
    result = cur.fetchone()
    
    if result:
        # Update existing item
        item_id, current_quantity = result
        new_quantity = current_quantity + quantity
        if new_quantity > 0:
            cur.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (new_quantity, item_id))
        else:
            cur.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    else:
        # Add new item
        if quantity > 0:
            cur.execute(
                "INSERT INTO inventory (name, quantity, expiration) VALUES (%s, %s, %s)",
                (name, quantity, expiration)
            )
    
    conn.commit()
    cur.close()
    conn.close()

# Get all items from the inventory
def get_inventory():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, quantity, to_char(expiration, 'YYYY-MM-DD')
        FROM inventory 
        ORDER BY expiration
    """)
    inventory = cur.fetchall()
    cur.close()
    conn.close()
    return inventory

# Get the latest taste profile
def get_taste_profile():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT profile FROM taste_profile ORDER BY id DESC LIMIT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else ""

# Save a new taste profile
def save_taste_profile(profile):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO taste_profile (profile) VALUES (%s)", (profile,))
    conn.commit()
    cur.close()
    conn.close()

# Create tables when the app starts
create_tables()

# Convert inventory to a string format
def get_inventory_string():
    inventory = get_inventory()
    return "\n".join([f"{item[0]}: {item[1]} (Expires: {item[2]})" for item in inventory])

# Create a summary of inventory modifications
def create_modification_summary(json_str):
    try:
        data = json.loads(json_str)
        items = data.get('items', [])
        summary = []
        for item in items:
            action = item.get('action')
            name = item.get('name')
            quantity = item.get('quantity', 1)
            expiration = item.get('expiration', 'estimated')
            if action == 'add':
                summary.append(f"Added {quantity} {name} (Expires: {expiration})")
            elif action == 'remove':
                summary.append(f"Removed {quantity} {name}")
        return "\n".join(summary)
    except json.JSONDecodeError:
        return "No valid JSON found in the response."
    except Exception as e:
        return f"Error processing inventory modification: {str(e)}"

# Process inventory modifications based on AI response
def process_inventory_modification(json_str):
    try:
        data = json.loads(json_str)
        items = data.get('items', [])
        for item in items:
            action = item.get('action')
            name = item.get('name')
            quantity = item.get('quantity', 1)
            expiration = item.get('expiration')
            
            if action == 'add':
                update_item_in_inventory(name, quantity, expiration)
            elif action == 'remove':
                update_item_in_inventory(name, -quantity, expiration)
        
        return "Inventory updated successfully."
    except json.JSONDecodeError:
        return "No valid JSON found in the response."
    except Exception as e:
        return f"Error processing inventory modification: {str(e)}"

# Display inventory as a pandas DataFrame
def display_inventory():
    inventory = get_inventory()
    df = pd.DataFrame(inventory, columns=["Name", "Quantity", "Expiration"])
    return df

# Toggle help display
def toggle_help():
    st.session_state.show_help = not st.session_state.get('show_help', False)

# Display help information
def show_help():
    if st.session_state.get('show_help', False):
        st.sidebar.info("""
        How to use ChefByte:
        1. Use the chat input to interact with the AI assistant.
        2. Modify your inventory by saying things like "Add 2 apples" or "Remove 1 milk".
        3. Ask for recipe suggestions based on your inventory and taste profile.
        4. Update your taste profile using the 'Taste Profile' button.
        5. View and manage your inventory in the sidebar.
        """)

# Initialize session state variables
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
    st.session_state["system_prompt"] = {
        "role": "system", 
        "content": """You are an AI assistant managing an inventory system and providing personalized recipe suggestions. When the user requests to modify the inventory, immediately output JSON with the modifications without asking for clarification. Follow these rules:

1. Always use JSON format for inventory modifications.
2. If quantity is not specified, assume 1.
3. If expiration is not specified, estimate a reasonable date based on the item type.
4. Use 'add' for adding items and 'remove' for removing items.
5. Always provide the expiration date in YYYY-MM-DD format.
6. Create a new entry only if an item with the same name and expiration doesn't exist.
7. Update quantity if the item already exists.
8. Remove items by subtracting their entire quantity.

Example JSON format:
{
    "items": [
        {"action": "add", "name": "Apple", "quantity": 5, "expiration": "2023-12-31"},
        {"action": "remove", "name": "Milk", "quantity": 2, "expiration": "2023-09-15"}
    ]
}

For recipe suggestions, consider the user's taste profile and current inventory. Provide 2-3 options with brief descriptions that align with preferences and available ingredients.

Only ask for clarification if the user's request is extremely ambiguous or impossible to act upon."""
    }

if "messages" not in st.session_state:
    st.session_state.messages = []

if "inventory_table" not in st.session_state:
    st.session_state.inventory_table = st.empty()

if "taste_profile" not in st.session_state:
    st.session_state.taste_profile = get_taste_profile()

# Update taste profile
def update_taste_profile():
    st.session_state.taste_profile = st.session_state.temp_taste_profile
    save_taste_profile(st.session_state.taste_profile)
    st.session_state.show_taste_profile_input = False

# Update inventory display
def update_inventory_display():
    df = display_inventory()
    st.session_state.inventory_table.table(df)

# Clear the entire inventory
def clear_inventory():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory")
    conn.commit()
    cur.close()
    conn.close()
    st.success("Inventory cleared successfully.")
    update_inventory_display()

# Sidebar layout
with st.sidebar:
    st.sidebar.title("📋 ChefByte Menu")
    
    st.button("ℹ️ Help", on_click=toggle_help)
    show_help()
    
    st.button("👤 Update Taste Profile", on_click=lambda: setattr(st.session_state, 'show_taste_profile_input', True))
    
    if st.button("🗑️ Clear Inventory"):
        clear_inventory()

    # Taste profile input form
    if st.session_state.get('show_taste_profile_input', False):
        with st.form("taste_profile_form"):
            st.text_area("Enter your taste profile:", key="temp_taste_profile", value=st.session_state.taste_profile)
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Save")
            with col2:
                closed = st.form_submit_button("Close")
            
            if submitted or closed:
                if submitted:
                    update_taste_profile()
                st.session_state.show_taste_profile_input = False

    st.subheader("🍽️ Your Pantry")
    st.session_state.inventory_table = st.empty()
    update_inventory_display()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input and AI response
if prompt := st.chat_input("What would you like to do?"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        inventory_string = get_inventory_string()
        full_system_prompt = st.session_state["system_prompt"].copy()
        full_system_prompt["content"] += f"\n\nCurrent Inventory:\n{inventory_string}\n\nUser's Taste Profile:\n{st.session_state.taste_profile}\n\nTime of user message: {timestamp}"

        messages = [full_system_prompt] + st.session_state.messages
        response = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=0.7
        ).choices[0].message.content

        # Process inventory modifications if the response is in JSON format
        if response.strip().startswith('{') and response.strip().endswith('}'):
            modification_summary = create_modification_summary(response)
            process_result = process_inventory_modification(response)
            
            full_response = f"{modification_summary}\n{process_result}"
            
            st.markdown(full_response)
            
            update_inventory_display()
        else:
            full_response = response
            st.markdown(full_response)
       
    st.session_state.messages.append({"role": "assistant", "content": full_response})