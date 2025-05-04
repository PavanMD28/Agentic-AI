import requests
from bs4 import BeautifulSoup
import faiss
import numpy as np
import json
from pathlib import Path
import webbrowser
from urllib.parse import urlparse
import hashlib
import sqlite3
import shutil
import os
from dotenv import load_dotenv
import asyncio
from google import genai
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial
from datetime import datetime, timedelta
import time
import google.generativeai as genai
from PIL import Image
import io

# Constants
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
INDEX_DIR = Path("faiss_index")
INDEX_DIR.mkdir(exist_ok=True)

def get_embedding(text: str) -> np.ndarray:
    """Get embedding from Ollama API"""
    response = requests.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def extract_text_from_url(url: str) -> list[tuple[str, str]]:
    """Extract text content from URL with element paths"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
            
        results = []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if len(element.get_text(strip=True)) > 50:  # Skip very short texts
                # Create CSS selector path
                path = generate_css_selector(element)
                results.append((element.get_text(strip=True), path))
        return results
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []

def generate_css_selector(element) -> str:
    """Generate a unique CSS selector for an element"""
    path = []
    while element and element.name:
        if element.get('id'):
            path.append(f"#{element['id']}")
            break
        elif element.get('class'):
            classes = '.'.join(element['class'])
            path.append(f"{element.name}.{classes}")
        else:
            siblings = element.find_previous_siblings(element.name)
            path.append(f"{element.name}:nth-of-type({len(siblings) + 1})")
        element = element.parent
    return ' > '.join(reversed(path))

def index_url(url: str, index, metadata: list) -> None:
    """Index a single URL"""
    start_time = time.time()
    print(f"Indexing {url}...")
    contents = extract_text_from_url(url)
    
    for text, selector in contents:
        embedding = get_embedding(text)
        if index.ntotal == 0:
            # Initialize index with correct dimensions
            dimension = len(embedding)
            index = faiss.IndexFlatL2(dimension)
            
        index.add(embedding.reshape(1, -1))
        metadata.append({
            "url": url,
            "text": text,
            "selector": selector
        })
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken to index {url}: {elapsed_time:.2f} seconds")
    return index

def search_content(query: str, top_k: int = 3) -> list[dict]:
    """Search indexed content and return matches with URLs"""
    # Load index and metadata
    index = faiss.read_index(str(INDEX_DIR / "web_index.bin"))
    with open(INDEX_DIR / "metadata.json", "r") as f:
        metadata = json.load(f)
    
    # Get query embedding and search
    query_vec = get_embedding(query).reshape(1, -1)
    D, I = index.search(query_vec, top_k)
    
    results = []
    for idx in I[0]:
        results.append(metadata[idx])
    return results

def main():
    # Initialize index and metadata
    index = faiss.IndexFlatL2(0)
    metadata = []
    
    print("Fetching Chrome history (limited to 20 most recent URLs)...")
    urls = get_chrome_history()
    print(f"\nFound {len(urls)} URLs in Chrome history")
    
    # Print all URLs before processing
    print("\nURLs to be processed:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    # Ask user if they want to continue
    choice = input("\nDo you want to continue processing these URLs? (y/n): ")
    if choice.lower() != 'y':
        print("Exiting...")
        return
    
    # Add timing for overall process
    total_start_time = time.time()
    
    # Add a counter and limit
    processed_count = 0
    max_urls = 20  # Changed to 20 URLs limit
    
    # Index URLs with limit
    for url in urls:
        if processed_count >= max_urls:
            print(f"Reached limit of {max_urls} URLs. Stopping indexing...")
            break
            
        try:
            index = index_url(url, index, metadata)
            processed_count += 1
            print(f"Processed {processed_count}/{max_urls} URLs")
        except Exception as e:
            print(f"Error indexing {url}: {e}")
    
    # Calculate and display total time
    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time
    print(f"\nTotal time taken: {total_elapsed_time:.2f} seconds")
    print(f"Average time per URL: {(total_elapsed_time/processed_count):.2f} seconds")
    
    # Save index and metadata
    faiss.write_index(index, str(INDEX_DIR / "web_index.bin"))
    with open(INDEX_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Example search
    while True:
        query = input("Enter search query (or 'q' to quit): ")
        if query.lower() == 'q':
            break
            
        results = search_content(query)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Found in: {result['url']}")
            print(f"Text: {result['text'][:200]}...")
            
        if results:
            choice = input("\nEnter result number to open (or press Enter to skip): ")
            if choice.isdigit() and 1 <= int(choice) <= len(results):
                result = results[int(choice)-1]
                # First open the webpage
                highlight_and_open(result['url'], result['selector'])
                
                # Then perform the analysis
                print("\nAnalyzing the content...")
                loop = asyncio.get_event_loop()
                analysis = loop.run_until_complete(analyze_content(result['text']))
                
                # Display analysis results
                print("\nSummary:")
                print(analysis['summary'])
                print("\nDetailed Analysis:")
                print(analysis['analysis'])
            print(f"\nOriginal Text: {result['text'][:200]}...")
            
        if results:
            choice = input("\nEnter result number to open (or press Enter to skip): ")
            if choice.isdigit() and 1 <= int(choice) <= len(results):
                result = results[int(choice)-1]
                highlight_and_open(result['url'], result['selector'])

def highlight_and_open(url: str, selector: str) -> None:
    """Open URL and inject highlighting JavaScript"""
    # Create a temporary HTML file with highlighting script
    html = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="0;url={url}">
        <script>
            window.onload = function() {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    element.style.backgroundColor = 'yellow';
                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                }}
            }};
        </script>
    </head>
    <body>Redirecting...</body>
    </html>
    """
    temp_path = INDEX_DIR / "redirect.html"
    temp_path.write_text(html)
    webbrowser.open(str(temp_path))

def get_chrome_history():
    """Get Chrome history for the last 15 days, limited to 20 most recent URLs"""
    history_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\History')
    history_copy = "chrome_history_temp"
    urls = []
    
    try:
        shutil.copy2(history_path, history_copy)
        conn = sqlite3.connect(history_copy)
        cursor = conn.cursor()
        
        fifteen_days_ago = int((datetime.now() - timedelta(days=15)).timestamp() * 1000000)
        cursor.execute("""
            SELECT url, title, last_visit_time 
            FROM urls 
            WHERE last_visit_time > ? 
            ORDER BY last_visit_time DESC
            LIMIT 20
        """, (fifteen_days_ago,))
        
        for row in cursor.fetchall():
            url = row[0]
            # Skip unwanted URLs (chrome://, about:, edge://, meet.google.com, youtube.com, gmail)
            if not any(url.startswith(prefix) for prefix in [
                'chrome://', 'about:', 'edge://', 
                'https://meet.google.com', 'https://www.meet.google.com',
                'https://youtube.com', 'https://www.youtube.com',
                'https://mail.google.com', 'https://gmail.com'
            ]):
                urls.append(url)
                
        conn.close()
        
    except Exception as e:
        print(f"Error accessing Chrome history: {e}")
    finally:
        if os.path.exists(history_copy):
            os.remove(history_copy)
            
    return urls

# Load environment variables from .env file
load_dotenv()

# Configure Gemini Flash 2.0
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

async def analyze_content(text: str) -> dict:
    """Analyze content using Gemini Flash 2.0"""
    try:
        # Generate content with timeout and configuration
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    contents=text,
                    generation_config={
                        "temperature": 0.1,
                        "candidate_count": 1,
                        "max_output_tokens": 1024,
                    }
                )
            ),
            timeout=20
        )
        
        # Generate comprehensive analysis
        analysis_prompt = f"""Please analyze this text and provide:
        1. Main topics and themes
        2. Key insights and takeaways
        3. Detailed sentiment analysis
        4. Important entities and their relationships
        5. Writing style and tone analysis
        6. Content structure analysis
        7. Recommendations based on the content
        
        Text: {text}
        """
        
        analysis_response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    contents=analysis_prompt,
                    generation_config={
                        "temperature": 0.1,
                        "candidate_count": 1,
                        "max_output_tokens": 1024,
                    }
                )
            ),
            timeout=20
        )
        
        return {
            "summary": response.text,
            "analysis": analysis_response.text
        }
    except TimeoutError:
        print("Analysis timed out!")
        return {
            "summary": "Analysis timed out",
            "analysis": "Analysis timed out"
        }
    except Exception as e:
        print(f"Error in content analysis: {e}")
        return {
            "summary": f"Error: {str(e)}",
            "analysis": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    main()