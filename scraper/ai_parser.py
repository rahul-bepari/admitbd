import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_circular(raw_text, university_name):
    """Send raw text to Groq and extract structured admission data."""

    prompt = f"""
You are an assistant that extracts university admission information from text.

Extract the following fields from the text below and return ONLY a valid JSON object.
If a field is not found, use null for dates/numbers and "Not specified" for text.

Fields to extract:
- apply_start: application start date (YYYY-MM-DD format)
- apply_end: application end date (YYYY-MM-DD format)
- min_ssc_gpa: minimum SSC GPA required (number)
- min_hsc_gpa: minimum HSC GPA required (number)
- application_fee: application fee in taka (number)
- eligible_groups: which groups can apply e.g. "Science, Business, Humanities"
- required_documents: list of required documents as a single string

University: {university_name}

Text:
{raw_text[:3000]}

Return ONLY the JSON object, no explanation, no markdown.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        # Clean up in case Groq adds markdown
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        data = json.loads(result_text)
        return data

    except Exception as e:
        print(f"Error parsing with Groq: {e}")
        return None