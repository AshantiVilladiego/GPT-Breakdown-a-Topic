from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import re
from markupsafe import Markup
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Format function
def format_explanation(raw_text):
    # Bold formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', raw_text)
    
    # Italics for markdown headings (# ...)
    text = re.sub(r'^\s*#+\s*(.*)', r'<em>\1</em>', text, flags=re.MULTILINE)

    # Style lettered headers (A. Something)
    text = re.sub(
        r'^(?P<letter>[A-Z])\.\s+(?P<title>.+)$',
        r'<div class="lettered-header">\g<letter>. \g<title></div>',
        text,
        flags=re.MULTILINE
    )

    # Lists
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


# Only Gemini is used
def explain_topic(topic):
# ... (Your explain_topic function is fine) ...
    prompt = f"""
    Break down the topic: "{topic}" as if you're teaching a complete beginner.

    Organize the explanation using the following structure:

        A. Market Research
            1. Target Audience
            2. Competition
            3. Trends

        B. Business Plan
            1. Goals and Objectives
            2. Budget
            3. Marketing Strategy

        C. Legal Requirements
            1. Business Registration
            2. Taxation
            3. Insurance

        D. Equipment and Supplies
            1. Necessary Tools
            2. Materials
            3. Software (if applicable)

        E. Production Process
            1. Step-by-step Overview
            2. Tools or Techniques
            3. Quality Control
            4. Packaging

        F. Product Range
            1. Types of Products or Services
            2. Customization Options
            3. Bundling or Packages

        G. Pricing Strategy
            1. Cost Analysis
            2. Competitive Pricing
            2. Promotions and Discounts

        H. Marketing and Sales
            1. Online Presence
            2. Social Media Strategy
            3. Offline Marketing
            4. Partnerships

        I. Customer Service
            1. Communication
            2. Feedback Collection
            3. After-sales Support

        J. Growth and Expansion
            1. New Product Ideas
            2. Scaling Strategies
            3. Diversification Opportunities

        End with a short summary of what it takes to succeed in this business or field.
        """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini error: {str(e)}"

# Route for the initial page load (GET request)
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# New API route to handle AJAX POST requests
@app.route("/api/breakdown", methods=["POST"])
def api_breakdown():
    data = request.json
    topic = data.get("topic")
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
    
    raw_explanation = explain_topic(topic)
    explanation = str(format_explanation(raw_explanation))
    
    return jsonify({"explanation": explanation})


if __name__ == "__main__":
    app.run(debug=True)