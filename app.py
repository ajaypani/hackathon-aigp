import os
from flask import Flask, render_template, request
import openai
import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Back, Style
from utils import get_moderation, get_response
from flask import Flask
load_dotenv()

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

app = Flask(__name__, template_folder='templates')
#app = Flask(_name_)

@app.route("/")
def home():
    #return 'hello'
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def chat():
    # os.system("cls" if os.name == "nt" else "clear")
    # keep track of previous questions and answers
    previous_questions_and_answers = []
    while True:
        # new_question = input("What can I get you?: ")
        new_question = request.form.get("question")
        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            # print("Sorry, you're question didn't pass the moderation check:")
            # for error in errors:
            error_messages = [
                error
                for error in errors
            ]
            #     print(error)
            # continue
            return {"response": "Sorry, your question didn't pass the moderation check:", "errors": error_messages}
        response = get_response(INSTRUCTIONS, previous_questions_and_answers, new_question)

        # add the new question and answer to the list of previous questions and answers
        previous_questions_and_answers.append((new_question, response))

        # print the response
        return {"response": response}
        
if __name__ == "_main_":
    app.run(debug=True)