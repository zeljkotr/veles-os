from .loader import load_all_knowledge


def search_knowledge(query, limit=3):
    """
    Search local knowledge.
    """

    knowledge = load_all_knowledge()

    query_words = query.lower().split()

    results = []

    for document in knowledge:

        content = document.get("content", "").lower()

        score = 0

        for word in query_words:

            if word in content:
                score += 1

            if word in document.get("name", "").lower():
                score += 2

        if score > 0:

            results.append(
                {
                    "score": score,
                    "name": document["name"],
                    "path": document["path"],
                    "content": document["content"]
                }
            )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:limit]


def get_knowledge_context(query):
    """
    Prepare retrieved knowledge for the LLM.
    """

    results = search_knowledge(query)

    if not results:
        return ""

    context = "LOCAL KNOWLEDGE:\n\n"

    for item in results:

        context += (
            f"--- {item['name']} ---\n"
            f"{item['content']}\n\n"
        )

    return context