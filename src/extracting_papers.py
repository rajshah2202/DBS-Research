import requests
from xml.etree import ElementTree as ET
import requests
import os

def search_pmc(query, max_results=10):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    pmc_ids = []
    retstart = 0
    batch_size = 20  # Number of results per batch

    while len(pmc_ids) < max_results:
        search_url = f"{base_url}esearch.fcgi?db=pmc&term={query}&retmax={batch_size}&retstart={retstart}"
        response = requests.get(search_url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            ids = [id_elem.text for id_elem in root.findall('.//Id')]
            if not ids:
                break  # No more results
            pmc_ids.extend(ids)
            retstart += batch_size
        else:
            break  # Stop if there's an error

        if len(ids) < batch_size:
            break  # No more results to fetch

    return pmc_ids[:max_results]

def fetch_pmc_details(pmc_ids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    articles = []

    # Fetch details in chunks (to avoid too large requests)
    for i in range(0, len(pmc_ids), 20):
        batch_ids = pmc_ids[i:i+20]  # Process in batches of 20
        fetch_url = f"{base_url}efetch.fcgi?db=pmc&id={','.join(batch_ids)}&retmode=xml"
        response = requests.get(fetch_url)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for article in root.findall('.//article'):
                title = article.find('.//article-title').text if article.find('.//article-title') is not None else "No Title"
                pmcid = article.find('.//article-id[@pub-id-type="pmc"]').text
                doi = article.find('.//article-id[@pub-id-type="doi"]').text if article.find('.//article-id[@pub-id-type="doi"]') is not None else "No DOI"
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                articles.append({"title": title, "pmcid": pmcid, "doi": doi, "pdf_url": pdf_url})
        else:
            print(f"Error fetching details for IDs {batch_ids}")

    return articles

def download_pdf(pdf_url, title):
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
        
        # Send a GET request to the PDF URL with headers
        response = requests.get(pdf_url, headers=headers, stream=True)
        
        # Check if the response is successful
        if response.status_code == 200:
            # Check if the content type is a PDF
            content_type = response.headers.get('Content-Type')
            if 'application/pdf' in content_type:
                # Clean title to create a valid filename
                safe_title = "".join(x for x in title if (x.isalnum() or x in "._- ")).strip()
                filename = f"../papers/{}/{safe_title}.pdf".replace(" ", "_")
                
                # Save the PDF content to a file
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                print(f"Downloaded PDF: {filename}")
            else:
                print(f"Failed to download PDF: {title} - Not a PDF file")
        elif response.status_code == 403:
            print(f"Failed to download PDF: {title} - HTTP Status: 403 (Forbidden). Try manual download.")
        else:
            print(f"Failed to download PDF: {title} - HTTP Status: {response.status_code}")

    except requests.RequestException as e:
        print(f"Error downloading PDF: {title} - {e}")

articles = fetch_pmc_details(pmc_ids)
print("PMC Articles:", articles)
query = "DBS in refractory depression"
pmc_ids = search_pmc(query, max_results=1)
print("PMC IDs:", pmc_ids)
for article in articles:
    download_pdf(article['pdf_url'], article['title'])