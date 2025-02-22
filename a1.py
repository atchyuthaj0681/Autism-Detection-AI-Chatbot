from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from waitress import serve

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up Gemini API
GEMINI_API_KEY = "AIzaSyAHdugnvoNWIqp-T6cgXj2Phbkse_076yA"  # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Store user data (sessions)
user_data = {}

# System prompt for generating autism-related questions
SYSTEM_PROMPT = """You are an AI chatbot designed to detect autism traits based on user responses.
You will ask the user 20 context-aware questions related to social behavior, communication, routines, and sensory sensitivities.
Generate the next question based on the previous answer to maintain logical flow."""

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_response = data.get("response", "").lower()
    user_id = data.get("user_id", "default_user")

    if user_id not in user_data:
        user_data[user_id] = {"score": 0, "questions_asked": 0, "chat_history": []}

    user_session = user_data[user_id]
    user_session["chat_history"].append({"user": user_response})

    # Autism scoring: +1 for responses suggesting autism traits
    positive_responses = ["yes", "yeah", "yup", "absolutely", "sometimes", "often", "always", "true"]
    autism_detected = any(word in user_response for word in positive_responses)

    if autism_detected:
        user_session["score"] += 1

    # Generate analysis based on current response
    analysis_prompt = f"Analyze the user's response: '{user_response}'. Does this indicate any autism-related traits? Provide a brief explanation."
    
    try:
        response = model.generate_content(analysis_prompt)
        analysis_result = response.text.strip()
    except Exception as e:
        analysis_result = "Unable to analyze this response at the moment."

    # Generate "How to Improve" suggestions only if response indicates autism traits
    improvement_suggestions = "No specific improvements needed."
    if autism_detected:
        improvement_prompt = f"Based on the user's response: '{user_response}', suggest how they can improve in social interaction, communication, or daily routines."
        try:
            response = model.generate_content(improvement_prompt)
            improvement_suggestions = response.text.strip()
        except Exception as e:
            improvement_suggestions = "Unable to generate improvement suggestions at this time."

    # Stop after 20 questions and provide final assessment
    if user_session["questions_asked"] >= 20:
        score = user_session["score"]
        
        # Determine autism level based on score
        if score >= 14:
            level = "High likelihood of autism"
            description = "Your responses indicate a strong likelihood of autism traits. Consider consulting a specialist for further evaluation."
        elif score >= 8:
            level = "Moderate likelihood of autism"
            description = "Your responses suggest some autism-related traits. You might benefit from professional advice."
        else:
            level = "Low likelihood of autism"
            description = "Your responses do not strongly indicate autism traits."

        return jsonify({
            "question": "End of assessment.",
            "score": score,
            "level": level,
            "description": description,
            "analysis": analysis_result,
            "improvement": improvement_suggestions
        })

    # Generate next question based on chat history
    prompt = SYSTEM_PROMPT + f"\nUser responses so far: {user_session['chat_history']}. Generate the next question."
    try:
        response = model.generate_content(prompt)
        next_question = response.text.strip()
    except Exception as e:
        next_question = "I'm having trouble generating the next question. Please try again later."

    user_session["questions_asked"] += 1
    user_session["chat_history"].append({"bot": next_question})

    return jsonify({
        "question": next_question,
        "analysis": analysis_result,
        "improvement": improvement_suggestions
    })

if __name__ == "__main__":
    print("Running production server with Waitress...")
    serve(app, host="0.0.0.0", port=5000)
