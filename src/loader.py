import json                        
import os                          
import fitz                       
from langchain_core.documents import Document           
from langchain_text_splitters import RecursiveCharacterTextSplitter  


def load_scraped_data(filepath: str = "data/raw/scraped_data.json") -> list:
    """
    Load scraped website content and return as LangChain Document objects.
    
    Args:
        filepath: Path to the scraped_data.json file
        
    Returns:
        List of Document objects with content and metadata
    """
    # Check the file exists before trying to open it
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Scraped data not found at {filepath}. "
            "Run: python -m src.scrapper first."
        )
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    documents = []  # Will hold all LangChain Document objects
    
    for campus, pages in data.items():
        for page in pages:
            doc = Document(
                page_content=page["content"],
                metadata={
                    "source": page["url"],
                    "campus": campus,
                    "type": "webpage"
                }
            )
            documents.append(doc)
    
    print(f"Loaded {len(documents)} web pages from {filepath}")
    return documents


def load_pdfs(pdf_dir: str = "data/pdfs/") -> list:
    """
    Load all PDF files from a directory and return as Document objects.
    
    Args:
        pdf_dir: Directory containing PDF files
        
    Returns:
        List of Document objects, one per PDF page (or whole PDF)
    """
    documents = []
    
    # Create directory if it doesn't exist (avoids crash if folder is empty)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"  No PDF files found in {pdf_dir} — skipping PDF loading")
        return []
    
    for filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, filename)
        
        try:
            # Open the PDF with PyMuPDF
            pdf = fitz.open(pdf_path)
            
            # Determine which campus based on filename convention
            # Name your PDFs like: nigeria_brochure.pdf or italy_handbook.pdf
            if "nigeria" in filename.lower():
                campus = "nigeria"
            elif "italy" in filename.lower():
                campus = "italy"
            else:
                campus = "general"  # Falls into both campus searches
            
            # Extract text from ALL pages of the PDF
            full_text = ""
            for page_num, page in enumerate(pdf):
                page_text = page.get_text()  # Extract text from this page
                full_text += f"\n[Page {page_num + 1}]\n{page_text}"
            
            # Close the PDF file handle
            pdf.close()
            
            # Create Document object
            doc = Document(
                page_content=full_text,
                metadata={
                    "source": filename,
                    "campus": campus,
                    "type": "pdf"
                }
            )
            documents.append(doc)
            print(f"  ✓ Loaded PDF: {filename} ({campus})")
            
        except Exception as e:
            print(f"  ✗ Error loading {filename}: {e}")
    
    return documents



def chunk_documents(documents: list, chunk_size: int = 800, chunk_overlap: int = 150) -> list:
    """
    Split documents into smaller chunks for embedding.
    
    Args:
        documents: List of LangChain Document objects
        chunk_size: Maximum characters per chunk
        chunk_overlap: Characters shared between adjacent chunks
        
    Returns:
        List of chunked Document objects (more items, smaller text each)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Try these separators in order — stop at first that works
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    
    # Add chunk index to metadata (helps with debugging)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    
    print(f"Split {len(documents)} documents → {len(chunks)} chunks")
    return chunks

def prepare_all_chunks() -> list:
    """
    Full pipeline: load web pages + PDFs, chunk them all, return chunks.
    
    Returns:
        Combined list of all chunked Documents from both campuses
    """
    print("\n📄 Loading documents...")
    
    # Load web pages
    web_docs = load_scraped_data()
    
    # Load PDFs (optional — if folder is empty, returns [])
    pdf_docs = load_pdfs()
    
    # Combine all documents
    all_docs = web_docs + pdf_docs
    print(f"  Total documents before chunking: {len(all_docs)}")
    
    # Chunk everything together
    print("\n  Chunking documents...")
    chunks = chunk_documents(all_docs)
    
    return chunks


# Entry point for testing this module directly
if __name__ == "__main__":
    chunks = prepare_all_chunks()
    # Preview the first chunk
    print(f"\nFirst chunk preview:")
    print(f"  Content: {chunks[0].page_content[:200]}...")
    print(f"  Metadata: {chunks[0].metadata}")
