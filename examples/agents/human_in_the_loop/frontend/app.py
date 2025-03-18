import streamlit as st
import uuid
from agent import (
    InvokeAgent,
    CompleteReturnControl,
    ProvideAgentConfirmation,
    Some_Api_Call,
)


st.title("HR Assistant")


def clear_session_state():
    # Clear all the session state variables
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def handle_submit_time_off():
    # This function will be called when the form is submitted
    ndays = st.session_state.roc_number_of_days
    sdate = st.session_state.roc_start_date
    print(f"Number of Days: {ndays}")
    print(f"Start Date: {sdate}")
    s = f"Requesting time off starting {sdate} for {ndays} days"
    st.session_state.messages.append({"role": "user", "content": s})
    roc_payload = st.session_state.roc_payload
    roc_payload["number_of_days"] = ndays
    roc_payload["start_date"] = sdate
    Some_Api_Call(ndays, sdate)
    resp = CompleteReturnControl(st.session_state.session_id, roc_payload)
    print(f"Got ROC completion response from agent: {resp}")
    st.session_state.messages.append({"role": "assistant", "content": resp})


def handle_confirm_time_off():
    # This function will be called when the user confirms action
    print("Confirming time off")
    st.session_state.messages.append(
        {"role": "user", "content": "User confirming time off"}
    )
    roc_payload = st.session_state.roc_payload
    roc_payload["action"] = "CONFIRM"
    resp = ProvideAgentConfirmation(st.session_state.session_id, roc_payload)
    print(f"Got ROC completion response from agent: {resp}")
    st.session_state.messages.append({"role": "assistant", "content": resp})


def handle_reject_time_off():
    # This function will be called when user rejects action
    print("Rejecting time off")
    st.session_state.messages.append(
        {"role": "user", "content": "User canceling time off request"}
    )
    roc_payload = st.session_state.roc_payload
    roc_payload["action"] = "DENY"
    resp = ProvideAgentConfirmation(st.session_state.session_id, roc_payload)
    print(f"Got ROC completion response from agent: {resp}")
    st.session_state.messages.append({"role": "assistant", "content": resp})


# Add this button to your UI
if st.button("Clear Session"):
    clear_session_state()
    st.success("Session data cleared!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "123"

print(f"Using session: {st.session_state.session_id}")
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        try:
            response = InvokeAgent(st.session_state.session_id, prompt)
            print(f"Got response from agent: {response}")

            if response["type"] == "returnControl":
                # create a table with the return control data
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Giving user option to edit time off request before submitting",
                    }
                )
                with st.form("return_control_form"):
                    st.write("Time Off Request")
                    number_of_days = st.number_input(
                        "Number of Days",
                        step=0.25,
                        value=float(response["number_of_days"]),
                        key="roc_number_of_days",
                    )
                    start_date = st.date_input(
                        "Start Date", value=response["start_date"], key="roc_start_date"
                    )
                    st.form_submit_button(
                        label="Submit", on_click=handle_submit_time_off
                    )
                    st.session_state.roc_payload = response
            elif response["type"] == "confirmation":
                # display confirm / deny actions
                message = f"Would you like to confirm your time off starting {response["start_date"]} for {response["number_of_days"]} days?"
                st.write(message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": message}
                )
                st.session_state.roc_payload = response
                st.button("Confirm", on_click=handle_confirm_time_off)
                st.button("Reject", on_click=handle_reject_time_off)
            else:
                # Add assistant response to chat history if not doing ROC
                st.write(response["message"])
                st.session_state.messages.append(
                    {"role": "assistant", "content": response["message"]}
                )

        except Exception as e:
            print(e)
            response = "Sorry, I had an error. Please try again."
            st.write(response)
