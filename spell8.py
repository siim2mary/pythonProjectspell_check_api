import streamlit as st
from autocorrect import Speller
import requests
import pyperclip

def download_nltk_resources():
    import nltk
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
    try:
        nltk.data.find('corpora/omw-1.4')
    except LookupError:
        nltk.download('omw-1.4', quiet=True)

download_nltk_resources()

def check_spelling_grammar(text):
    spell = Speller()  # Initialize the spell checker
    spelling_corrections = {}  # Dictionary to store spelling corrections

    # Correct each word's spelling in the input text and gather corrections
    corrected_words = [spell(word) for word in text.split()]
    for original_word, corrected_word in zip(text.split(), corrected_words):
        if original_word != corrected_word:  # If a word is corrected, store it
            spelling_corrections[original_word] = {"spelling": corrected_word}

    # Join the corrected words into a sentence for further grammar checking
    corrected_sentence = " ".join(corrected_words)

    # Send a request to the LanguageTool API
    response = requests.post(
        'https://api.languagetool.org/v2/check',
        data={'text': corrected_sentence, 'language': 'en-US'}
    )
    result = response.json()

    grammar_corrections = {}
    for match in result['matches']:
        grammar_corrections[match['offset']] = {
            'context': match['context']['text'],
            'message': match['message'],
            'suggestions': [replacement['value'] for replacement in match['replacements']]
        }

    corrected_text = corrected_sentence
    for match in reversed(result['matches']):
        start = match['offset']
        end = start + match['length']
        if match['replacements']:
            corrected_text = corrected_text[:start] + match['replacements'][0]['value'] + corrected_text[end:]

    return spelling_corrections, grammar_corrections, corrected_text

def get_definitions(word):
    response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    if response.status_code == 200:  # Check if the API request was successful
        return response.json()[0]["meanings"][0]["definitions"][0]["definition"]  # Return the first definition
    else:
        return None  # Return None if the word is not found

def main():
    st.title("Spelling and Grammar Check App")  # Set the title of the app
    st.sidebar.title("Options")  # Set the title of the sidebar

    # Add a download button in the sidebar (currently does not download anything specific)
    st.sidebar.download_button("Download Corrections", "Corrections")

    # Add a share button in the sidebar to copy corrected text to clipboard
    if st.sidebar.button("Share"):
        pyperclip.copy("Corrected Text")  # Copy placeholder text to clipboard
        st.write("Text copied to clipboard!")  # Notify the user

    # Create a text area for the user to input the text they want to check
    text = st.text_area("Enter text to check for spelling and grammar errors:")

    # When the user clicks the "Check" button, run the spell and grammar check
    if st.button("Check"):
        spelling_corrections, grammar_corrections, corrected_text = check_spelling_grammar(text)

        # If there are any spelling or grammar corrections, display them
        if spelling_corrections or grammar_corrections:
            st.write("**Spelling Corrections:**")
            for word, correction in spelling_corrections.items():
                st.write(f"- **Original:** {word}")
                st.write(f"  - Spelling correction: {correction['spelling']}")
                definition = get_definitions(correction['spelling'])  # Fetch the definition of the corrected word
                if definition:
                    st.write(f"  - Definition: {definition}")  # Display the definition if found

            st.write("**Grammar Corrections:**")
            for offset, correction in grammar_corrections.items():
                st.write(f"- **Error Context:** {correction['context']}")
                st.write(f"  - **Message:** {correction['message']}")
                st.write(f"  - **Suggestions:** {', '.join(correction['suggestions'])}")

            # Display the fully corrected text
            st.write("**Corrected Text:**")
            st.markdown(f"<p style='color: green;'>{corrected_text}</p>", unsafe_allow_html=True)
        else:
            st.write("No corrections needed! Your text is perfect!")  # Message if no corrections are needed

# Run the app
if __name__ == "__main__":
    main()
