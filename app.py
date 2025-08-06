from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os
import google.generativeai as genai
import requests
import openai
import json
import re
from markupsafe import Markup
import requests

# Load environment variables from .env
load_dotenv()
print("Hugging Face API Key:", os.getenv("HUGGINGFACE_API_KEY"))  # Debug print
print(os.getenv("OPENAI_API_KEY"))

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Set up API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")

def format_explanation(raw_text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', raw_text)
    text = re.sub(r'^\s*#+\s*(.*)', r'<em>\1</em>', text, flags=re.MULTILINE)

    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            formatted_lines.append(f"<li>{line.strip()[2:]}</li>")
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(line)
    if in_list:
        formatted_lines.append('</ul>')
    return Markup('\n'.join(formatted_lines))

def query_huggingface(prompt, model="mistralai/Mistral-7B-Instruct-v0.1"):
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {huggingface_api_key}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif "generated_text" in result:
                return result["generated_text"]
            elif "output" in result:
                return result["output"]
            else:
                return str(result)
        except json.JSONDecodeError:
            return "Error: Hugging Face response was not valid JSON."
    else:
        return f"Hugging Face error {response.status_code}: {response.text}"
    
# --- Explain function ---
def explain_topic(topic, provider):
    prompt = f"""
        Break down the topic: "{topic}" as if you're teaching a complete beginner.

        Organize the explanation using the following structure:

        1. Market Research
        - Target Audience
        - Competition
        - Trends

        2. Business Plan
        - Goals and Objectives
        - Budget
        - Marketing Strategy

        3. Legal Requirements
        - Business Registration
        - Taxation
        - Insurance

        4. Equipment and Supplies
        - Necessary Tools
        - Materials
        - Software (if applicable)

        5. Production Process
        - Step-by-step Overview
        - Tools or Techniques
        - Quality Control
        - Packaging

        6. Product Range
        - Types of Products or Services
        - Customization Options
        - Bundling or Packages

        7. Pricing Strategy
        - Cost Analysis
        - Competitive Pricing
        - Promotions and Discounts

        8. Marketing and Sales
        - Online Presence
        - Social Media Strategy
        - Offline Marketing
        - Partnerships

        9. Customer Service
        - Communication
        - Feedback Collection
        - After-sales Support

        10. Growth and Expansion
            - New Product Ideas
            - Scaling Strategies
            - Diversification Opportunities

        End with a short summary of what it takes to succeed in this business or field
        """
    if provider == "huggingface":
        try:
            import json

            api_url = "https://api-inference.huggingface.co/models/bigscience/bloomz-560m"
            headers = {
                "Authorization": f"Bearer {huggingface_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": f"Explain the topic: {topic}",
                "options": {"wait_for_model": True}
            }

            response = requests.post(api_url, headers=headers, json=payload)

            # Check if response is OK
            if response.status_code != 200:
                return f"HuggingFace error: {response.status_code} - {response.text}"

            # Try decoding JSON response
            try:
                result = response.json()
            except json.JSONDecodeError:
                return "Error: Unable to decode response from HuggingFace."

            # Extract generated text safely
            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            else:
                return f"HuggingFace API returned unexpected format: {result}"

        except Exception as e:
            return f"Unexpected HuggingFace error: {str(e)}"
    
    elif provider == "gemini":
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(prompt)
            
            return response.text  

        except Exception as e:
            return f"Gemini error: {str(e)}"


    elif provider == "openai":
        try:
            # Use openai.ChatCompletion directly
            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),  # fallback to gpt-4o
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            return response.choices[0].message["content"]

        except Exception as e:
            return f"OpenAI SDK error: {str(e)}"

        except Exception as e:
            return f"OpenAI SDK error: {str(e)}"

def get_breakdown(topic):
    try:
        # 1. Try OpenAI GPT-4
        openai_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Break down the topic '{topic}' in a structured and organized way. Use headings and bullet points. Make it beginner-friendly."}
            ]
        )
        return openai_response.choices[0].message.content

    except Exception as e_openai:
        print("OpenAI failed:", e_openai)

        try:
            # 2. Fallback to Gemini (Google Generative AI)
            gemini_prompt = f"Break down the topic '{topic}' in a structured and organized way. Use headings and bullet points. Make it beginner-friendly."
            gemini_response = genai.chat(messages=[gemini_prompt])
            return gemini_response.last

        except Exception as e_gemini:
            print("Gemini failed:", e_gemini)
            return "Sorry, all AI providers are currently unavailable. Please try again later."

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form["topic"]
        provider = request.form["provider"]

        print("Selected provider:", provider)
        print("Topic entered:", topic)

        raw_explanation = explain_topic(topic, provider)
        explanation = format_explanation(raw_explanation)

        # Always update the session with new values
        session["explanation"] = str(explanation)
        session["topic"] = topic
        session["provider"] = provider

        return redirect(url_for("index"))

    # GET request (initial or after POST redirect)
    topic = session.get("topic", "")
    provider = session.get("provider", "")
    explanation = session.get("explanation", "")

    return render_template("index.html", topic=topic, provider=provider, explanation=explanation)


if __name__ == "__main__":
    app.run(debug=True)

