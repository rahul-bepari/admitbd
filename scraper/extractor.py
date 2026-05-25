import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_from_url(url):
    """Detects if URL is PDF or webpage, extracts text accordingly."""
    try:
        response = requests.get(url, timeout=10, verify=False)
        content_type = response.headers.get("Content-Type", "")

        if "pdf" in content_type or url.endswith(".pdf"):
            return extract_from_pdf(response.content)
        else:
            return extract_from_html(response.text)

    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None


def extract_from_html(html):
    """Extracts visible text from an HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Clean up blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def extract_from_pdf(pdf_bytes):
    """Extracts text from PDF bytes."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

    return text.strip()