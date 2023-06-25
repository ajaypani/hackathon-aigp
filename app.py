import os
import logging

import openai
from flask import Flask, render_template, request
from dotenv import load_dotenv
from utils import get_response, get_moderation

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """
Your instructions...
"""

app = Flask(__name__, template_folder='templates')

@app.route("/")
def home():
    logger.info("Rendering home page")
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def chat():
    new_question = request.form.get("question")
    logger.info("Received new question: %s", new_question)

    # keep track of previous questions and answers
    previous_questions_and_answers = []

    # check the question is safe
    errors = get_moderation(new_question)
    if errors:
        error_messages = [
            error
            for error in errors
        ]
        logger.warning("Question failed moderation check: %s", new_question)
        logger.warning("Moderation errors: %s", error_messages)
        return {"response": "Sorry, your question didn't pass the moderation check:", "errors": error_messages}

    response = get_response(INSTRUCTIONS, previous_questions_and_answers, new_question)
    logger.info("Generated response: %s", response)

    # add the new question and answer to the list of previous questions and answers
    previous_questions_and_answers.append((new_question, response))

    return {"response": response}

if __name__ == "__main__":
    app.run(debug=True)
