from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from waitress import serve


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ✅ Update API Key
GEMINI_API_KEY = "AIzaSyBwzNdfPbPDRq2aQdyKIp5fQXhdgYrk8ik"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Use "gemini-pro" Model Correctly
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

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

    print(f"User Response: {user_response}")  # Debugging

    # Autism scoring logic
    positive_responses = ["yes", "yeah", "yup", "absolutely", "sometimes", "often", "always", "true"]
    autism_detected = any(word in user_response for word in positive_responses)

    if autism_detected:
        user_session["score"] += 1

    # Analysis generation
    analysis_prompt = f"Analyze the user's response: '{user_response}'. Does this indicate any autism-related traits?"
    try:
        response = model.generate_content(analysis_prompt)
        analysis_result = response.text.strip()
    except Exception as e:
        print("Error generating analysis:", str(e))
        analysis_result = "Unable to analyze this response at the moment."

    # Improvement suggestions
    improvement_suggestions = "No specific improvements needed."
    if autism_detected:
        improvement_prompt = f"Suggest improvements based on user's response: '{user_response}'."
        try:
            response = model.generate_content(improvement_prompt)
            improvement_suggestions = response.text.strip()
        except Exception as e:
            print("Error generating improvement suggestions:", str(e))
            improvement_suggestions = "Unable to generate suggestions at this time."

    # Stop after 20 questions
    if user_session["questions_asked"] >= 20:
        score = user_session["score"]
        level = "High" if score >= 14 else "Moderate" if score >= 8 else "Low"
        description = (
            "Strong likelihood of autism traits. Consult a specialist." if level == "High" else
            "Some autism-related traits. Professional advice recommended." if level == "Moderate" else
            "Responses do not strongly indicate autism traits."
        )
        return jsonify({"question": "End of assessment.", "score": score, "level": level, "description": description, "analysis": analysis_result, "improvement": improvement_suggestions})

    # Generate next question
    prompt = SYSTEM_PROMPT + f"\nUser responses so far: {user_session['chat_history']}. Generate the next question."
    try:
        response = model.generate_content(prompt)
        print("Generated Question:", response.text)  # Debugging
        next_question = response.text.strip()
    except Exception as e:
        print("Error generating question:", str(e))
        next_question = "I'm having trouble generating the next question. Please try again later."

    user_session["questions_asked"] += 1
    user_session["chat_history"].append({"bot": next_question})

    return jsonify({"question": next_question, "analysis": analysis_result, "improvement": improvement_suggestions})

if __name__ == "__main__":
    print("Running production server with Waitress...")
    serve(app, host="0.0.0.0", port=5000)
