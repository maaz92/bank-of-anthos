import streamlit as st
# import crud
# from models import ChatCreate, UserCreate
import re
from utils import get_time_in_user_timezone, get_user_profile, write_message
from langgraph_agent import generate_response, clear_chat
import uuid
import rest_clients
import jwt

# Page Config
st.set_page_config(
    page_title="Cymbal Bank",
    page_icon=":bank:",  # Emoji icon for a shopping cart
    layout="centered",
    initial_sidebar_state="expanded"
)

def get_bot_intro_message():
    return {
        "role": "assistant",
        "content": "I am Ross, I can help you with your banking. How can I assist you today?"
    }

def write_bot_intro_message():
    st.session_state.messages = [
        get_bot_intro_message()
    ]

def create_new_chat_if_required():
    if 'chat_id' in st.session_state and st.session_state.chat_id is not None:
        return False
    st.session_state.chat_id = str(uuid.uuid1())
    # crud.create_new_chat(ChatCreate(id = st.session_state.chat_id, user_id = st.session_state.current_user.id, 
    #                                 messages=[st.session_state.messages[0]]))
    return True

def append_message_to_chat():
    return None
    # crud.append_message_to_chat(st.session_state.chat_id, st.session_state.messages[-1])

@st.dialog("Login Attempt")
def login_attempt(email, password):
    with st.spinner('Logging in...'):
        if validate_username(email) is None or validate_password(password) is None:
            st.error("Invalid Data")
        else:
            success, message, user = login_user(email, password)
            if success: 
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# @st.dialog("Chat Preview")
# def chat_preview_dialog(chat):
#     created_at = get_time_in_user_timezone(chat.created_at)
#     st.caption(created_at.strftime("%Y-%m-%d %H:%M"))
#     for message in chat.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

with st.sidebar:
    st.image("images/cymbal.svg", use_container_width=True)
    st.text("")
    if 'logged_in' in st.session_state and st.session_state.logged_in == True:
        col1, col2 = st.columns(2)
        with col1:
            logout = st.button("Logout", type="primary")
        with col2:
            new_chat = st.button("New ✍️", type="primary")
        if logout:
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.messages = []
            if 'chat_id' in st.session_state:
                clear_chat()
                st.session_state.chat_id = None
            st.rerun()

        if new_chat:
            st.session_state.messages = []
            clear_chat()
            st.session_state.chat_id = None
            write_bot_intro_message()
            st.rerun()
        # chats = crud.get_all_chats_for_user(st.session_state.current_user.id)
        # st.caption(f"History: {len(chats)} {'chat' if len(chats) == 1 else 'chats'}")
        # for chat in chats:
        #     shortened_text = textwrap.shorten(chat.messages[1]["content"], width=40, placeholder="...")
        #     if st.button(shortened_text, key=chat.id, type="secondary"):
        #         chat_preview_dialog(chat)

def validate_name(name):
    name_pattern = r"^[A-Za-z\s-]{2,}$"
    return re.fullmatch(name_pattern, name)

def validate_username(username: str):
    # Verify username contains only 2-15 alphanumeric or underscore characters
    return re.match(r"\A[a-zA-Z0-9_]{2,15}\Z", username)
    # raise UserWarning('username must contain 2-15 alphanumeric characters or underscores')

def validate_password(password):
    if password is not None and len(password.strip()) > 0:
        return True
    return None

def login_user(email, password):
    login_response = rest_clients.user_service_client.login(email, password)
    if login_response["is_credentials_valid"] == False:
        return False, "Invalid username or password.", ""
    decoded_payload = jwt.decode(login_response["token"], options={"verify_signature": False})
    st.session_state["token"] = login_response["token"]
    return True, "Login successful.", decoded_payload

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.logged_in:
    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username", value='testuser')
        if username:
            if validate_username(username) is None:
                st.error("Username must contain only 2-15 alphanumeric or underscore characters")
        password = st.text_input("Password", type="password", value='bankofanthos')
        if password:
            if not validate_password(password):
                st.error("Password cannot be empty.")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            login_attempt(username, password)
else:
    st.title("Ross, your banking assistant")
    if "messages" not in st.session_state or st.session_state.messages == []:
        write_bot_intro_message()

    def handle_submit(message):
        """
        Submit handler:
        """
        with st.spinner('Thinking...'):
            # Call the agent
            append_message_to_chat()
            response = generate_response(message)
            write_message('assistant', response)
            append_message_to_chat()

    for message in st.session_state.messages:
        write_message(message['role'], message['content'], save=False)

    if question := st.chat_input("Ask something..."):
        write_message('user', question)
        if create_new_chat_if_required():
            user_profile = get_user_profile()
            question += '\n ' + str(user_profile)
            print(user_profile)
        handle_submit(question)