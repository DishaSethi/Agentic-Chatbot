import os
import psycopg2
from dotenv import load_dotenv
from google import genai
from pgvector.psycopg2 import register_vector
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Setup Environment & Fix User-Agent Warning
os.environ["USER_AGENT"] = "StudentProjectMentor/1.0"
load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
DATABASE_URL = os.getenv("DB_URL")

if not DATABASE_URL:
    raise ValueError("🚨 ERROR: DATABASE_URL is missing! Check your .env file.")
if not GEMINI_API_KEY:
    raise ValueError("🚨 ERROR: GEMINI_API_KEY is missing! Check your .env file.")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Target Practical, Free-Tier & Student-Friendly Documentation
SOURCES = [
    {
        "url": "https://vercel.com/docs/limits/overview",
        "category": "Free-Tier Serverless Limits (Prevent Over-engineering)"
    },
    {
        "url": "https://supabase.com/docs/guides/getting-started/architecture",
        "category": "Modern BaaS & Database (PostgreSQL/Auth)"
    },
    {
        "url": "https://12factor.net/",
        "category": "Pragmatic App Architecture (Clean Code for Students)"
    },
    {
        "url": "https://restfulapi.net/",
        "category": "REST API Best Practices"
    }
]

def run_ingestion():
    # Connect to Neon
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cursor = conn.cursor()

    print("🧹 Wiping old enterprise data from the database...")
    # THIS IS CRITICAL: It deletes the old AWS/GCP data so the AI stops thinking like an enterprise!
    cursor.execute("TRUNCATE TABLE best_practices;")

    # Ensure the URL column exists
    cursor.execute("ALTER TABLE best_practices ADD COLUMN IF NOT EXISTS source_url TEXT;")

    # Loop through all the sources
    for source in SOURCES:
        target_url = source["url"]
        category = source["category"]

        print(f"\n🌍 Scraping: {target_url} [{category}]")

        try:
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

        except Exception as e:
            print(f"❌ Failed to scrape {target_url}. Error: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n🚀 Mass Ingestion complete! The AI is now a practical Student Mentor.")

if __name__ == "__main__":
    run_ingestion()