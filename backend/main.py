from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import json
from datetime import datetime
from fastapi.staticfiles import StaticFiles

app = FastAPI()

EXCLUDED_DOMAINS = [
    'g.co', 'facebook.com', 'instagram.com', 'x.com', 'twitter.com',
    'pinterest.com', 'shopify.com', 'edpb.europa.eu'
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/114.0.0.0 Safari/537.36"
}

class CrawlRequest(BaseModel):
    url: str

@app.post("/api/crawl")
def crawl(data: CrawlRequest):
    def generate():
        input_url = data.url.strip()
        if not input_url.startswith("http://") and not input_url.startswith("https://"):
            input_url = "https://" + input_url
        parsed = urlparse(input_url)
        domain = parsed.netloc.replace("www.", "")
        start_url = input_url

        visited = set()
        to_visit = [start_url]
        outbound_links = set()
        broken_links = set()
        mailto_links = set()
        pages_scanned = 0

        def normalize_domain(d): return d.lower().replace("www.", "")

        while to_visit:
            url = to_visit.pop(0)
            if url in visited:
                continue
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                if response.status_code == 404:
                    broken_links.add(url)
                    yield json.dumps({"log": f"❌ 404 Not Found: {url}"}) + "\n"
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                visited.add(url)
                yield json.dumps({"log": f"✅ Scanned: {url}"}) + "\n"

                for a in soup.find_all("a", href=True):
                    href = a['href'].strip()

                    if href == "#" or href.lower().startswith(("javascript:", "tel:")):
                        continue

                    if href.startswith("mailto:"):
                        try:
                            email_domain = href.split("@")[1].lower()
                            if domain not in email_domain and href not in mailto_links:
                                mailto_links.add(href)
                                yield json.dumps({"log": f"📧 Mailto: {href}"}) + "\n"
                        except IndexError:
                            pass
                        continue

                    full_url = urldefrag(urljoin(url, href))[0]
                    parsed_href = urlparse(full_url)
                    netloc = normalize_domain(parsed_href.netloc)
                    normalized_url = parsed_href._replace(netloc=netloc).geturl()

                    if not netloc or domain in netloc:
                        if normalized_url not in visited and normalized_url not in to_visit:
                            to_visit.append(normalized_url)
                    else:
                        if any(skip in netloc for skip in EXCLUDED_DOMAINS):
                            continue
                        if normalized_url not in outbound_links:
                            outbound_links.add(normalized_url)
                            yield json.dumps({"log": f"🔗 Outbound: {normalized_url}"}) + "\n"
                            try:
                                ext_resp = requests.get(normalized_url, headers=HEADERS, timeout=10)
                                if ext_resp.status_code == 404:
                                    broken_links.add(normalized_url)
                                    yield json.dumps({"log": f"❌ 404 External: {normalized_url}"}) + "\n"
                            except Exception as e:
                                broken_links.add(normalized_url)
                                yield json.dumps({"log": f"❌ Failed to load: {normalized_url} ({str(e)})"}) + "\n"

                pages_scanned += 1
                progress = int((pages_scanned / (pages_scanned + len(to_visit))) * 100)
                yield json.dumps({"progress": progress, "scanned": pages_scanned}) + "\n"

            except Exception as e:
                broken_links.add(url)
                yield json.dumps({"log": f"❌ Failed to crawl: {url} ({str(e)})"}) + "\n"

        # Export to PDF
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"crawl_results_{domain.replace('.', '_')}_{timestamp}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        text = c.beginText(40, 750)
        text.setFont("Helvetica", 12)
        text.textLine("Terry Ecom Link Checker Results")
        text.textLine(f"Checked Domain: {domain}")
        text.textLine(f"Timestamp: {timestamp}")
        text.textLine("")

        text.textLine("📧 Error Mailto Links:")
        if mailto_links:
            for m in sorted(mailto_links):
                text.textLine(m)
        else:
            text.textLine("ZERO errors")

        text.textLine("")
        text.textLine("🔗 Error Outbound Links:")
        if outbound_links:
            for o in sorted(outbound_links):
                text.textLine(o)
        else:
            text.textLine("ZERO errors")

        text.textLine("")
        text.textLine("❌ Broken Links (404s or failed):")
        if broken_links:
            for b in sorted(broken_links):
                text.textLine(b)
        else:
            text.textLine("ZERO errors")

        # Footer with social links
        text.textLine("")
        text.textLine("---------------------------")
        text.textLine("🌐 https://www.terryecom.com")
        text.textLine("✉️ terry@terryecom.com")
        text.textLine("📷 https://www.instagram.com/terryecom/")
        text.textLine("𝕏 https://x.com/TerryEcom")

        c.drawText(text)
        c.save()

        yield json.dumps({
            "log": "✅ Crawl complete",
            "download": f"/api/download/{filename}"
        }) + "\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/api/download/{filename}")
def download(filename: str):
    return FileResponse(path=filename, filename=filename)

from pathlib import Path
static_path = Path(__file__).parent.parent / "frontend-dist"
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
