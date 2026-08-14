import os
import psycopg2
from pgvector.psycopg2 import register_vector
from google import genai
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.getenv("DB_URL")
gemini_client=genai.Client()

SAMPLE_RULES = [
    {
        "category": "High Availability",
        "content": "For 99.99% availability, databases and caches must be deployed across multiple Availability Zones (Multi-AZ). Single points of failure are unacceptable for enterprise architectures."
    },
    {
        "category": "Caching Strategy",
        "content": "Always place a distributed cache like Redis in front of PostgreSQL for read-heavy workloads. This is required to achieve sub-50ms latency."
    },
    {
        "category": "Security & Auth",
        "content": "All endpoints must enforce TLS 1.3 encryption. APIs should validate JWT tokens on connection initialization to mitigate unauthorized access."
    },
    {
        "category": "Scalability",
        "content": "Use message queues (RabbitMQ/Kafka) or Pub/Sub to decouple stateful application instances and allow horizontal autoscaling under peak traffic loads."
    }
]


def seed():
    conn=psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cursor=conn.cursor()

    print("🌱 Embedding and seeding rules into Neon DB using Gemini...")
    for item in SAMPLE_RULES:
        embed_response=gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=item["content"]
        )

        embedding=embed_response.embeddings[0].values

        cursor.execute(
            "INSERT INTO best_practices (category, content, embedding) VALUES (%s, %s, %s);",
            (item["category"], item["content"], embedding)
        )


    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database successfully seeded!")


if __name__ =="__main__":
    seed()