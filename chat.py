import streamlit as st
from language_tool_python import LanguageTool
import openai
from utils import debounce  # Import the debounce function

# Set OpenAI API key
openai.api_key = 'your_openai_api_key'

# Initialize LanguageTool for grammar correction
tool = LanguageTool('en-US')

# Define the debounce function
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def debounce(func, duration):
    """
    A debounce function that delays the execution of a function until after a specified duration
    of inactivity. This prevents double activations and improves performance.
    
    Args:
    - func: The function to be debounced.
    - duration: The duration (in milliseconds) to wait before executing the function.
    """
    def debounced_function(*args, **kwargs):
        import time
        key = str((args, kwargs))
        last_executed = st.session_state.get('debounce_last_executed', {})
        if key in last_executed:
            if time.time() - last_executed[key] < duration / 1000:
                return
        last_executed[key] = time.time()
        st.session_state['debounce_last_executed'] = last_executed
        return func(*args, **kwargs)
    return debounced_function

# Function for grammar correction
@debounce
def correct_grammar(text):
    matches = tool.check(text)
    corrected_text = tool.correct(text)
    return corrected_text

# Function for content suggestion
@debounce
def generate_content(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100
    )
    return response.choices[0].text.strip()

# App title
st.set_page_config(page_title="🦙💬 Llama 2 Chatbot")

# Replicate Credentials
with st.sidebar:
    st.title('🦙💬 Llama 2 Chatbot')
    st.write('This chatbot is created using the open-source Llama 2 LLM model from Meta.')
    
    replicate_api = st.text_input('Enter Replicate API token:', type='password')
    if not replicate_api.startswith('r8_') or len(replicate_api) != 40:
        st.warning('Please enter a valid Replicate API token!', icon='⚠️')
    else:
        st.success('API key validated!', icon='✅')
        
    os.environ['REPLICATE_API_TOKEN'] = replicate_api
    
    st.subheader('Models and parameters')
    selected_model = st.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    
    temperature = st.slider('Temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.slider('Top P', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('Max Length', min_value=32, max_value=128, value=120, step=8)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat history
chat_history = ""
for message in st.session_state.messages:
    if message["role"] == "user":
        chat_history += f"You: {message['content']}\n"
    else:
        chat_history += f"Assistant: {message['content']}\n"

st.text_area("Chat History", value=chat_history, height=300, max_chars=None, key=None)

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Function to return to the social blog app
def return_to_blog_app():
    blog_app_url = "https://socialblogapp.netlify.app/"
    st.markdown(f"Redirecting to [Blog App]({blog_app_url})...")
    st.experimental_rerun()

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Add button to return to the social blog app
st.sidebar.button('Return to Blog App', on_click=return_to_blog_app)

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    output = replicate.run(llm, 
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature":temperature, "top_p":top_p, "max_length":max_length, "repetition_penalty":1})
    return output

# User-provided prompt
prompt = st.text_input('Type your message:', key='prompt')
if st.button('Send') and prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        # Correct grammar before sending prompt to generate response
        corrected_prompt = correct_grammar(prompt)
        # Generate content suggestion based on corrected prompt
        content_suggestion = generate_content(corrected_prompt)
        # Generate LLM response using the corrected prompt
        response = generate_llama2_response(corrected_prompt)
        full_response = ''
        for item in response:
            full_response += item
        # Append the content suggestion to the LLM response
        full_response += "\n\nContent Suggestion: " + content_suggestion
        st.session_state.messages.append({"role": "assistant", "content": full_response})