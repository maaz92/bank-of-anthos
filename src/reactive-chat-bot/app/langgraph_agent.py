import os
import sys
from typing import Literal
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st
import rest_clients
import utils

memory = InMemorySaver()

try:
    api_key = os.environ["GEMINI_API_KEY"]
except KeyError:
    print("Error: GEMINI_API_KEY environment variable is not set.")
    sys.exit(1)

@tool
def get_balance():
    """
    Gets the version of the user service
    Args: No Arguments
    Returns:
        int: The balance of the user's account in cents
    """
    return rest_clients.balance_service_client.get_balance()

@tool
def get_transaction_history():
    """
    Gets the last 5 transactions
    Args: No arguments
    Returns:
        list: A list of transactions ordered by their timestamps. Latest first
    """
    contacts_response = rest_clients.contacts_service_client.get_contacts()
    label_dict = {}
    for contact in contacts_response["contacts"]:
        label_dict[contact["account_num"]] = contact["label"]
    transactions_response = rest_clients.history_service_client.get_transaction_history()
    if transactions_response["request_successful"] is False:
        return "Error. Please try again"
    transaction_list = []
    for idx, transaction in enumerate(transactions_response['history']):
        account_number = transaction["fromAccountNum"]
        if transaction["fromAccountNum"] == utils.get_current_account_number():
            transaction_type = "DEBIT"
            account_number = transaction["toAccountNum"]
        else:
            transaction_type = "CREDIT"
        tr = {
            "date": transaction["timestamp"],
            "transaction_type": transaction_type,
            "account_number": account_number,
            "label": label_dict.get(account_number, ""),
            "amount": float(transaction["amount"]) / 100.0
        }
        transaction_list.append(tr)
        if idx > 4:
            break
    return transaction_list

@tool
def get_contacts():
    """
    Gets the list of user contacts
    Arguments: No Arguments
    Returns:
        list: A list of contacts
    """
    contacts_response = rest_clients.contacts_service_client.get_contacts()
    if contacts_response["request_successful"] is False:
        return "Error. Please try again"
    contacts_list = []
    for contact in contacts_response["contacts"]:
        contacts_list.append({
            "label": contact["label"],
            "account_number": contact["account_num"],
            "routing_number": contact["routing_num"],
            "is_external_account": contact["is_external"],
            "type": "depositor" if contact["is_external"] else "recipient",
        })
    return contacts_list

@tool
def add_depositor(account_number: str, routing_number: str, label: str):
    """
    Adds a depositor account to the user's contacts
    Arguments:
        account_number (str): The depositor account number. Exactly 10 digits (no spaces, no letters, no extra characters)
        routing_number (str): The depositor account routing number. Exactly 9 digits (no spaces, no letters, no extra characters)
        label (str): A label for the depositor. Must be >0 and <=30 chars, alphanumeric and spaces, can't start with space
    Returns:
        dict: is_successful(True/False) and optional errors(Containing a list of error messages)
    """
    return rest_clients.contacts_service_client.add_contact(
        account_num=account_number,
        routing_num=routing_number,
        label=label,
        is_external=True
    )

@tool
def add_recipient(account_number: str, label: str):
    """
    Adds a recipient account to the user's contacts
    Arguments:
        account_number (str): The depositor account number. Exactly 10 digits (no spaces, no letters, no extra characters)
        label (str): A label for the depositor. Must be >0 and <=30 chars, alphanumeric and spaces, can't start with space
    Returns:
        dict: is_successful(True/False) and optional errors(Containing a list of error messages)
    """
    return rest_clients.contacts_service_client.add_contact(
        account_num=account_number,
        label=label,
        is_external=False
    )

@tool
def deposit_money(from_account_number: str, from_routing_number: str, amount: float):
    """
    Deposit money from a depositor contact. Must already be a contact
    Arguments:
        from_account_number (str): The depositor account number. Exactly 10 digits (no spaces, no letters, no extra characters)
        from_routing_number (str): The depositor account routing number. Exactly 9 digits (no spaces, no letters, no extra characters)
        amount (float): Amount in US dollars.
    Returns:
        dict: is_successful(True/False)
    """
    return rest_clients.transactions_service_client.add_transaction(
        from_account_number=from_account_number,
        from_routing_number=from_routing_number,
        amount=int(100 * amount)
    )

@tool
def send_money(to_account_number: str, amount: float):
    """
    Send money from a recipient contact. Must already be a contact
    Arguments:
        to_account_number (str): The recipient account number. Exactly 10 digits (no spaces, no letters, no extra characters)
        amount (float): Amount in US dollars.
    Returns:
        dict: is_successful(True/False)
    """
    return rest_clients.transactions_service_client.add_transaction(
        to_account_number=to_account_number,
        amount=int(100 * amount)
    )

tools = [
    get_balance,
    get_transaction_history,
    get_contacts,
    add_depositor,
    add_recipient,
    deposit_money,
    send_money
]

# Create LLM class
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.4,
    max_retries=2,
    google_api_key=api_key,
)

# Bind tools to the model
llm_with_tools = llm.bind_tools(tools)

# Nodes
def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            llm_with_tools.invoke(
                [
                    SystemMessage(
                        content="""You are Ross an online banking assistant for Cymbal Bank. You can assist by doing only the following two types of tasks:
                        1. Show account balance
                        2. Show account number
                        3. List upto last 5 transactions(show date, type, account number, label, amount) in tabular format.
                        4. List depositor(show account number, routing number, label) in a tabular format.
                        5. List recipients(show account number number, label) in a tabular format.
                        6. List contacts(depositors and recipients) in separate tables.
                        7. Add a new depositor.
                        8. Deposit money to own account.
                        9. Add a new recipient.
                        10. Send money to a recipient.
Follow these for all the responses:
Return your responses as it will be displayed in a banking app chat.
Ask for confirmation after taking the details for:
1. adding depositor
2. adding recipient
3. making deposit
4. sending money.
External accounts are depositor accounts and internal accounts are recipient accounts
You are not allowed to use any external knowledge or information.
Only use the information provided in the context. Don't use your pretrained knowledge."""
                    )
                ] + state["messages"]
            )
        ]
    }

tools_by_name = {tool.name: tool for tool in tools}

def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    with st.expander("🔨 Tool Call", expanded=False):
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            st.write(f"Called tool :blue[{tool_call['name']}] with args :blue[{tool_call['args']}]")
            observation = tool.invoke(tool_call["args"])
            if observation is not None:
                st.write(f"Observation: ")
                st.json(observation)
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def should_continue(state: MessagesState) -> Literal["environment", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]
    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "Action"
    # Otherwise, we stop (reply to the user)
    return END

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("environment", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "Action": "environment",
        END: END,
    },
)
agent_builder.add_edge("environment", "llm_call")

# Compile the agent
agent = agent_builder.compile(checkpointer=memory)

# Show the agent
agent.get_graph().print_ascii()

def generate_response(message: str):
    config = {"configurable": {"thread_id": st.session_state.chat_id}}
    messages = [HumanMessage(content=message)]
    messages = agent.invoke({"messages": messages}, config)
    for m in messages["messages"]:
        m.pretty_print()
    return messages["messages"][-1].content

def clear_chat():
    if 'chat_id' in st.session_state and st.session_state.chat_id is not None:
        memory.delete_thread(st.session_state.chat_id)