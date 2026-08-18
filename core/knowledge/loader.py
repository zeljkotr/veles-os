from pathlib import Path


# Knowledge root directory
KNOWLEDGE_DIR = Path(__file__).resolve().parent


SUPPORTED_FILES = [
    ".md",
    ".txt"
]


def find_documents():
    """
    Find all supported documents in the knowledge directory.
    """

    documents = []

    for file in KNOWLEDGE_DIR.rglob("*"):

        if file.is_file() and file.suffix.lower() in SUPPORTED_FILES:

            documents.append(file)

    return documents


def load_document(file_path):
    """
    Load a single knowledge document.
    """

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return {
                "name": file_path.name,
                "path": str(file_path),
                "content": file.read()
            }

    except Exception as e:

        return {
            "name": file_path.name,
            "path": str(file_path),
            "error": str(e)
        }


def load_all_knowledge():
    """
    Load the complete knowledge base.
    """

    knowledge = []

    documents = find_documents()

    for document in documents:

        loaded = load_document(document)

        knowledge.append(loaded)

    return knowledge


def knowledge_count():
    """
    Return the number of available knowledge documents.
    """

    return len(find_documents())