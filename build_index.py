import asyncio
from src.scraper  import scrape_all
from src.loader   import prepare_all_chunks
from src.embedder import upload_to_pinecone

async def main():
    print("="*55)
    print("  RBS CHATBOT — INDEX BUILDER")
    print("="*55)

    print("\n[1/3] Scraping RBS websites…")
    await scrape_all()

    print("\n[2/3] Chunking documents…")
    chunks = prepare_all_chunks()

    print("\n[3/3] Uploading to Pinecone…")
    upload_to_pinecone(chunks, namespace="rbs")

    print("\nIndex build complete.")
    print("    Run the app: streamlit run app.py")

if __name__ == "__main__":
    asyncio.run(main())
