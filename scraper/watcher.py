import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from dotenv import load_dotenv
from scraper.extractor import extract_from_url
from scraper.ai_parser import parse_circular
from scraper.universities_config import UNIVERSITIES
import schedule
import time

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_university_id(short_name):
    """Get university ID from Supabase by short name."""
    result = supabase.table("universities").select("id").eq("short_name", short_name).execute()
    if result.data:
        return result.data[0]["id"]
    return None

def save_circular(university_id, data, source_url, raw_text):
    """Save parsed circular data to Supabase."""
    record = {
        "university_id": university_id,
        "apply_start": data.get("apply_start"),
        "apply_end": data.get("apply_end"),
        "min_ssc_gpa": data.get("min_ssc_gpa"),
        "min_hsc_gpa": data.get("min_hsc_gpa"),
        "application_fee": data.get("application_fee"),
        "eligible_groups": data.get("eligible_groups"),
        "required_documents": data.get("required_documents"),
        "source_url": source_url,
        "raw_text": raw_text[:2000]
    }
    supabase.table("circulars").insert(record).execute()
    print(f"  ✓ Saved to database")

def run_scraper():
    """Main function — scrape all universities and save to DB."""
    print("Starting AdmitBD scraper...")

    for uni in UNIVERSITIES:
        print(f"\nChecking {uni['name']}...")

        raw_text = extract_from_url(uni["notice_url"])
        if not raw_text:
            print(f"  ✗ Could not extract text")
            continue

        print(f"  ✓ Text extracted ({len(raw_text)} chars)")

        data = parse_circular(raw_text, uni["name"])
        if not data:
            print(f"  ✗ Could not parse with Groq")
            continue

        print(f"  ✓ Parsed: {data}")

        university_id = get_university_id(uni["short_name"])
        if not university_id:
            print(f"  ✗ University not found in DB")
            continue

        save_circular(university_id, data, uni["notice_url"], raw_text)

    print("\nScraper finished!")

def start_scheduler():
    """Run scraper daily at 8AM."""
    schedule.every().day.at("08:00").do(run_scraper)
    print("Scheduler started — will run daily at 8AM")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scraper()