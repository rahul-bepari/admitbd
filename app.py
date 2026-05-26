import os
from flask import Flask, render_template, request
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_universities():
    result = supabase.table("universities").select("*").execute()
    return result.data

def get_latest_circular(university_id):
    result = supabase.table("circulars").select("*")\
        .eq("university_id", university_id)\
        .order("created_at", desc=True)\
        .limit(1).execute()
    if result.data:
        return result.data[0]
    return None

def get_university_image(name):
    try:
        import requests
        # Try multiple search variations
        searches = [
            name.replace(" ", "_"),
            name.replace(",", "").replace(" ", "_"),
            name.split(",")[0].replace(" ", "_"),  # e.g. "Independent_University"
        ]
        for search in searches:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                img = data.get("originalimage", {}).get("source") or \
                      data.get("thumbnail", {}).get("source")
                if img:
                    return img
    except:
        pass
    return None


@app.route("/")
def home():
    universities = get_universities()
    return render_template("index.html", universities=universities)

@app.route("/universities")
def universities():
    universities = get_universities()
    return render_template("universities.html", universities=universities)

@app.route("/university/<int:uni_id>")
def university_detail(uni_id):
    result = supabase.table("universities").select("*").eq("id", uni_id).execute()
    uni = result.data[0] if result.data else None
    circular = get_latest_circular(uni_id)
    image_url = get_university_image(uni["name"]) if uni else None
    return render_template("university_detail.html", uni=uni, circular=circular, image_url=image_url)

@app.route("/checker", methods=["GET", "POST"])
def checker():
    matches = []
    ssc = hsc = None
    if request.method == "POST":
        ssc = float(request.form.get("ssc", 0))
        hsc = float(request.form.get("hsc", 0))
        circulars = supabase.table("circulars").select("*, universities(name, short_name, website, location)").execute()
        for c in circulars.data:
            min_ssc = c.get("min_ssc_gpa")
            min_hsc = c.get("min_hsc_gpa")
            if min_ssc is None or min_hsc is None:
                continue  # skip circulars with no GPA data
            if ssc >= min_ssc and hsc >= min_hsc:
                matches.append(c)
    return render_template("checker.html", matches=matches, ssc=ssc, hsc=hsc)

@app.route("/deadlines")
def deadlines():
    circulars = supabase.table("circulars").select("*, universities(name, short_name, location)")\
        .not_.is_("apply_end", "null")\
        .order("apply_end").execute()
    return render_template("deadlines.html", circulars=circulars.data)

@app.route("/advisor", methods=["GET", "POST"])
def advisor():
    answer = None
    question = None
    if request.method == "POST":
        question = request.form.get("question", "")

        # Get all universities + circulars from DB
        unis = supabase.table("universities").select("*").execute().data
        circulars = supabase.table("circulars").select("*, universities(name, short_name)").execute().data

        # Build context string for Groq
        context = "Here is the current university admission data in Bangladesh:\n\n"
        for c in circulars:
            uni_name = c.get("universities", {}).get("name", "Unknown")
            context += f"- {uni_name}: SSC min={c.get('min_ssc_gpa')}, HSC min={c.get('min_hsc_gpa')}, "
            context += f"Fee=৳{c.get('application_fee')}, Deadline={c.get('apply_end')}, "
            context += f"Groups={c.get('eligible_groups')}\n"

        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"You are AdmitBD, a helpful Bangladesh university admission advisor. Use this data to answer:\n{context}"},
                {"role": "user", "content": question}
            ],
            temperature=0.5
        )
        answer = response.choices[0].message.content

    return render_template("advisor.html", answer=answer, question=question)


if __name__ == "__main__":
    app.run(debug=True)