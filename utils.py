import streamlit as st

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
