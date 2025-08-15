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
    prompt = f"""
            Generate a business guide for {topic}.  
            The guide should follow this exact structure, with each subtopic written in one sentence only — short, concise, but knowledgeable.  
            Do not include specific examples unless they are generic to the business type in the prompt.  
            For the "Primary Equipment" line, automatically adapt it to the main equipment relevant to the business type.

            {topic} is a versatile and profitable business. Here’s a breakdown of the key aspects involved in starting and running a {topic} business.

            ### Market Research
            1. **Target Audience**: Identify your primary customers.
            2. **Competition**: Analyze the strengths and weaknesses of other businesses in the market.
            3. **Trends**: Stay updated on current and emerging industry trends.

            ### Business Plan
            1. **Goals and Objectives**: Define clear and measurable business goals.
            2. **Budget**: Outline all startup, operational, and projected revenue figures.
            3. **Marketing Strategy**: Develop a plan for promoting and positioning your business.

            ### Legal Requirements
            1. **Business Registration**: Register your business and comply with all legal formalities.
            2. **Taxation**: Understand and fulfill your business’s tax obligations.
            3. **Insurance**: Secure insurance coverage to mitigate potential risks.

            ### Equipment and Supplies
            1. **Primary Equipment**: Acquire [insert main equipment relevant to the business type] suited for professional production.
            2. **Materials**: Source high-quality materials necessary for creating your products or services.
            3. **Software/Tools**: Use appropriate digital or physical tools to design, manage, and deliver offerings.

            ### Production Process
            1. **Designing**: Develop appealing and functional product designs.
            2. **Printing**: Produce items with consistent quality and accuracy.
            3. **Cutting**: Prepare products to precise shapes and sizes.
            4. **Packaging**: Package products securely and attractively.

            ### Product/Service Range
            1. **Custom Offerings**: Provide tailored options that meet specific client needs.
            2. **Standard Offerings**: Offer ready-made solutions for general use.
            3. **Bundles/Packages**: Create grouped offerings or deals to increase sales value.

            ### Pricing Strategy
            1. **Cost Analysis**: Set prices based on accurate cost and profit calculations.
            2. **Competitive Pricing**: Align pricing with industry benchmarks.
            3. **Discounts and Packages**: Offer incentives to encourage higher-volume purchases.

            ### Marketing and Sales
            1. **Online Presence**: Maintain a professional digital platform to promote and sell.
            2. **Social Media**: Use online channels to build awareness and engagement.
            3. **Local Marketing**: Apply offline strategies to reach nearby customers.
            4. **Collaborations**: Partner with others to expand your reach and credibility.

            ### Customer Service
            1. **Communication**: Ensure clear, professional, and responsive interaction with customers.
            2. **Feedback**: Collect and apply customer feedback to improve.
            3. **After-sales Support**: Offer ongoing assistance after the sale.

            ### Growth and Expansion
            1. **New Offerings**: Continuously develop fresh products or services.
            2. **Wholesale/Scaling**: Expand operations to reach larger markets.
            3. **Diversification**: Enter related markets or introduce complementary offerings.

            Starting a {topic} involves thorough planning, creativity, and dedication. By focusing on quality, customer satisfaction, and effective marketing, you can build a successful and sustainable business.

            """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
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