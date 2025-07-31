from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
from markupsafe import Markup

# Initialize Flask
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for session

# Load API key and configure
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Format response into HTML
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

# Generate content
def explain_topic(topic):
    prompt = f"""Break down the topic '<strong>{topic}</strong>' in simple terms like you're teaching a beginner. Include:<br>
    - <span class="highlight">Summary</span><br>
    - <span class="highlight">Key concepts</span><br>
    - <span class="highlight">Real-world examples</span><br>
    - <span class="highlight">Why it matters</span>"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ An error occurred: {str(e)}"

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form["topic"]
        raw_explanation = explain_topic(topic)
        explanation = format_explanation(raw_explanation)

        # Save to session
        session["explanation"] = str(explanation)  # Store as string (Markup is serializable as str)
        session["topic"] = topic
        return redirect(url_for("index"))  # Redirect to avoid resubmission

    # On GET
    explanation = session.get("explanation", "")
    topic = session.get("topic", "")
    return render_template("index.html", explanation=explanation, topic=topic)

if __name__ == "__main__":
    app.run(debug=True)
