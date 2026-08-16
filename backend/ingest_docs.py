import os
import psycopg2
from dotenv import load_dotenv
from google import genai
from pgvector.psycopg2 import register_vector
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Setup Environment & Fix User-Agent Warning
os.environ["USER_AGENT"] = "SystemArchitectureAI/1.0"
load_dotenv() # Make sure your .env file is in the same folder as this script!

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
DATABASE_URL = os.getenv("DB_URL")

# --- ADD THIS SAFETY CHECK ---
if not DATABASE_URL:
    raise ValueError("🚨 ERROR: DATABASE_URL is missing! Check your .env file.")
if not GEMINI_API_KEY:
    raise ValueError("🚨 ERROR: GEMINI_API_KEY is missing! Check your .env file.")
# -----------------------------

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Target Real Documentation
SOURCES = [
    {
        "url": "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/reliability.html",
        "category": "Reliability & Fault Tolerance"
    },
    {
        "url": "https://cloud.google.com/blog/topics/solutions-how-tos/optimize-your-system-design-using-architecture-framework-principles",
        "category": "Cloud System Design"
    },
    {
        "url": "https://wiki.postgresql.org/wiki/Performance_Optimization",
        "category": "Database Scaling"
    }
]

def run_ingestion():
    # ... rest of your code stays exactly the same ...
    # Load: Connect to Neon just ONCE before the loop
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cursor = conn.cursor()

    # Add a source_url column if you haven't already!
    cursor.execute("ALTER TABLE best_practices ADD COLUMN IF NOT EXISTS source_url TEXT;")

    # Loop through all the sources
    for source in SOURCES:
        target_url = source["url"]
        category = source["category"]

        print(f"\n🌍 Scraping: {target_url} [{category}]")

        # 3. Extract: Scrape the raw HTML
        loader = WebBaseLoader(target_url)
        docs = loader.load()

        # 4. Transform: Chunk the massive document into 1000-character blocks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(docs)
        print(f"✂️ Split into {len(chunks)} conceptual chunks.")

        print("🧠 Generating embeddings and inserting into Neon DB...")
        for i, chunk in enumerate(chunks):
            # Embed the chunk using the modern SDK
            embed_response = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=chunk.page_content,
            )

            # The modern SDK returns embeddings differently depending on batching,
            # but for a single string, we access it like this:
            embedding = embed_response.embeddings[0].values

            # Insert into PostgreSQL
            cursor.execute(
                """
                INSERT INTO best_practices (category, content, embedding, source_url)
                VALUES (%s, %s, %s, %s);
                """,
                (category, chunk.page_content, embedding, target_url)
            )

        print(f"✅ Finished ingesting {category}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n🚀 Mass Ingestion complete! The AI is now smarter.")

if __name__ == "__main__":
    run_ingestion()