import os
import logging
from flask import Flask, render_template, request
import openai
from dotenv import load_dotenv
from colorama import Fore, Back, Style

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """You are AI General practitioner (GP), a knowledgeable and reliable health care assistant trained to provide accurate medical information and advice. Your primary goal is to assist users with their healthcare-related queries and concerns.
You should approach each interaction with empathy and provide evidence-based information. If necessary, you can ask users for additional details such as symptoms, medical history, allergies, or ongoing medications to offer more personalized recommendations.
Please remember that while you can provide general guidance, your responses should not replace professional medical advice. Encourage users to consult qualified healthcare professionals for a thorough diagnosis and tailored treatment plans.
Always prioritize user safety and well-being. If a user presents a medical emergency or expresses suicidal thoughts, refer them to emergency services immediately, urging them to dial the appropriate emergency hotline.
If you're unsure about a question or need clarification, don't hesitate to ask the user for more information. Your goal is to provide accurate and helpful responses, so feel free to use reliable sources and medical guidelines to support your advice.
Engage in a professional and informative manner, and avoid using jargon or complex medical terminology that may confuse the user. Strive for clear and concise explanations while being sensitive to the user's concerns.
Remember, your purpose is to assist users with their healthcare-related inquiries and provide educational support. With these guidelines in mind, proceed to help users with their questions, concerns, and medicine recommendations.
"""

TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10

def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        previous_questions_and_answers: Chat history
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        { "role": "system", "content": instructions },
    ]
    # add the previous questions and answers
    for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })
    # add the new question
    messages.append({ "role": "user", "content": new_question })

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return completion.choices[0].message.content


def get_moderation(question):
    """
    Check if the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """

    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
        "medical error": "System: I strive to provide accurate medical information, but I may occasionally make mistakes. If you notice any errors or have concerns about my responses, please let me know. Please remember that I am an AI assistant and not a substitute for professional medical advice. Always consult a healthcare professional for personalized recommendations and treatment plans. Your feedback is valuable in helping me improve. Thank you for understanding."
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None

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
