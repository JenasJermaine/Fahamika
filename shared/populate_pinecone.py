"""
Fahamika — Pinecone Content Population Script
Chunks text (constitution articles, civic content) into Pinecone vectors.

Usage:
  python shared/populate_pinecone.py

This script:
  1. Takes content items (articles, topics)
  2. Embeds each one using intfloat/multilingual-e5-base
  3. Upserts them into the Pinecone index

IMPORTANT: E5 models need a "passage: " prefix when embedding documents
           (and "query: " when embedding search queries — already done in retriever.py)
"""

import logging
import sys
from pathlib import Path

# Ensure the project root is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from shared.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("populate")

# ── Sample content: Key articles from the Kenyan Constitution ──
# Replace/extend this list with your full constitution content.
# Each item: {id, topic, content, language, chapter, article}

SAMPLE_CONTENT = [
    {
        "id": "constitution-art-54",
        "topic": "Rights of Persons with Disabilities",
        "content": (
            "Article 54 of the Constitution of Kenya 2010: "
            "(1) A person with any disability is entitled— "
            "(a) to be treated with dignity and respect and to be addressed and referred to in a manner that is not demeaning; "
            "(b) to access educational institutions and facilities for persons with disabilities that are integrated into society to the extent compatible with the interests of the person; "
            "(c) to reasonable access to all places, public transport and information; "
            "(d) to use Sign language, Braille or other appropriate means of communication; and "
            "(e) to access materials and devices to overcome constraints arising from the person's disability. "
            "(2) The State shall ensure the progressive implementation of the principle that at least five percent of the members of the public in elective and appointive bodies are persons with disabilities."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "54",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-38",
        "topic": "Voting Rights and Political Participation",
        "content": (
            "Article 38 of the Constitution of Kenya 2010: "
            "(1) Every citizen is free to make political choices, which includes the right— "
            "(a) to form, or participate in forming, a political party; "
            "(b) to participate in the activities of, or recruit members for, a political party; or "
            "(c) to campaign for a political party or cause. "
            "(2) Every citizen has the right to free, fair and regular elections based on universal suffrage and the free expression of the will of the electors for— "
            "(a) any elective public body or office established under this Constitution; or "
            "(b) any office of any political party of which the citizen is a member. "
            "(3) Every adult citizen has the right, without unreasonable restrictions— "
            "(a) to be registered as a voter; "
            "(b) to vote by secret ballot in any election or referendum; and "
            "(c) to be a candidate for public office, or office within a political party of which the citizen is a member and, if elected, to hold office."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "38",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-43",
        "topic": "Economic and Social Rights (Health, Housing, Food, Water, Social Security, Education)",
        "content": (
            "Article 43 of the Constitution of Kenya 2010: "
            "(1) Every person has the right— "
            "(a) to the highest attainable standard of health, which includes the right to health care services, including reproductive health care; "
            "(b) to accessible and adequate housing, and to reasonable standards of sanitation; "
            "(c) to be free from hunger, and to have adequate food of acceptable quality; "
            "(d) to clean and safe water in adequate quantities; "
            "(e) to social security; and "
            "(f) to education. "
            "(2) A person shall not be denied emergency medical treatment. "
            "(3) The State shall provide appropriate social security to persons who are unable to support themselves and their dependants."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "43",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-27",
        "topic": "Equality and Freedom from Discrimination",
        "content": (
            "Article 27 of the Constitution of Kenya 2010: "
            "(1) Every person is equal before the law and has the right to equal protection and equal benefit of the law. "
            "(2) Equality includes the full and equal enjoyment of all rights and fundamental freedoms. "
            "(3) Women and men have the right to equal treatment, including the right to equal opportunities in political, economic, cultural and social spheres. "
            "(4) The State shall not discriminate directly or indirectly against any person on any ground, including race, sex, pregnancy, marital status, health status, ethnic or social origin, colour, age, disability, religion, conscience, belief, culture, dress, language or birth. "
            "(5) A person shall not discriminate directly or indirectly against another person on any of the grounds specified or contemplated in clause (4)."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "27",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-56",
        "topic": "Affirmative Action for Minorities and Marginalised Groups",
        "content": (
            "Article 56 of the Constitution of Kenya 2010: "
            "The State shall put in place affirmative action programmes designed to ensure that minorities and marginalised groups— "
            "(a) participate and are represented in governance and other spheres of life; "
            "(b) are provided special opportunities in educational and economic fields; "
            "(c) are provided special opportunities for access to employment; "
            "(d) develop their cultural values, languages and practices; and "
            "(e) have reasonable access to water, health services and infrastructure."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "56",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-10",
        "topic": "National Values and Principles of Governance",
        "content": (
            "Article 10 of the Constitution of Kenya 2010: "
            "(1) The national values and principles of governance in this Article bind all State organs, State officers, public officers and all persons whenever any of them— "
            "(a) applies or interprets this Constitution; "
            "(b) enacts, applies or interprets any law; or "
            "(c) makes or implements public policy decisions. "
            "(2) The national values and principles of governance include— "
            "(a) patriotism, national unity, sharing and devolution of power, the rule of law, democracy and participation of the people; "
            "(b) human dignity, equity, social justice, inclusiveness, equality, human rights, non-discrimination and protection of the marginalised; "
            "(c) good governance, integrity, transparency and accountability; and "
            "(d) sustainable development."
        ),
        "language": "en",
        "chapter": "2 — The Republic",
        "article": "10",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-35",
        "topic": "Access to Information",
        "content": (
            "Article 35 of the Constitution of Kenya 2010: "
            "(1) Every citizen has the right of access to— "
            "(a) information held by the State; and "
            "(b) information held by another person and required for the exercise or protection of any right or fundamental freedom. "
            "(2) Every person has the right to the correction or deletion of untrue or misleading information that affects the person. "
            "(3) The State shall publish and publicise any important information affecting the nation."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "35",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-46",
        "topic": "Consumer Rights",
        "content": (
            "Article 46 of the Constitution of Kenya 2010: "
            "(1) Consumers have the right— "
            "(a) to goods and services of reasonable quality; "
            "(b) to the information necessary for them to gain full benefit from goods and services; "
            "(c) to the protection of their health, safety, and economic interests; and "
            "(d) to compensation for loss or injury arising from defects in goods or services. "
            "(2) Parliament shall enact legislation to provide for consumer protection and for fair, honest and decent advertising. "
            "(3) This Article applies to goods and services offered by public entities or private persons."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "46",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-48",
        "topic": "Access to Justice",
        "content": (
            "Article 48 of the Constitution of Kenya 2010: "
            "The State shall ensure access to justice for all persons and, if any fee is required, it shall be reasonable and shall not impede access to justice."
        ),
        "language": "en",
        "chapter": "4 — Bill of Rights",
        "article": "48",
        "source": "Constitution of Kenya 2010",
    },
    {
        "id": "constitution-art-174",
        "topic": "Objects of Devolution (County Government Services)",
        "content": (
            "Article 174 of the Constitution of Kenya 2010: "
            "The objects of the devolution of government are— "
            "(a) to promote democratic and accountable exercise of power; "
            "(b) to foster national unity by recognising diversity; "
            "(c) to give powers of self-governance to the people and enhance the participation of the people in the exercise of the powers of the State and in making decisions affecting them; "
            "(d) to recognise the right of communities to manage their own affairs and to further their development; "
            "(e) to protect and promote the interests and rights of minorities and marginalised communities; "
            "(f) to promote social and economic development and the provision of proximate, easily accessible services throughout Kenya; "
            "(g) to ensure equitable sharing of national and local resources throughout Kenya; "
            "(h) to facilitate the decentralisation of State organs, their functions and services, from the capital of Kenya; and "
            "(i) to enhance checks and balances and the separation of powers."
        ),
        "language": "en",
        "chapter": "11 — Devolved Government",
        "article": "174",
        "source": "Constitution of Kenya 2010",
    },
]


# ═══════════════════════════════════════════════════════════════════
#  Population Logic
# ═══════════════════════════════════════════════════════════════════

def populate(content_items: list[dict], batch_size: int = 50):
    """
    Embed content items and upsert them into Pinecone.

    Args:
        content_items: List of dicts with id, topic, content, language, chapter, article, source.
        batch_size: How many items to process in one Pinecone upsert batch.
    """
    # 1. Connect to Pinecone
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index = pc.Index(config.PINECONE_INDEX_NAME)

    # 2. Load the embedding model
    model_name = config.EMBEDDING_MODEL
    logger.info(f"Loading embedding model: {model_name} ...")
    model = SentenceTransformer(model_name)
    logger.info("Model loaded.")

    # 3. Process in batches
    total = len(content_items)
    for i in range(0, total, batch_size):
        batch = content_items[i : i + batch_size]
        vectors = []

        for item in batch:
            # E5 models need "passage: " prefix for document embeddings
            text_to_embed = f"passage: {item['content']}"
            embedding = model.encode(text_to_embed).tolist()

            vectors.append({
                "id": item["id"],
                "values": embedding,
                "metadata": {
                    "topic": item["topic"],
                    "content": item["content"],
                    "language": item.get("language", "en"),
                    "chapter": item.get("chapter", ""),
                    "article": item.get("article", ""),
                    "source": item.get("source", ""),
                },
            })

        # Upsert batch
        index.upsert(vectors=vectors, namespace="civic-content")
        logger.info(f"Upserted {i + len(batch)}/{total} vectors")

    logger.info(f"✅ Done. {total} items populated into '{config.PINECONE_INDEX_NAME}'.")


def list_items(index_name: str | None = None):
    """Quick check: list a few items from the index to verify population."""
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index = pc.Index(index_name or config.PINECONE_INDEX_NAME)

    # Fetch a few known IDs to verify
    sample_ids = [item["id"] for item in SAMPLE_CONTENT[:3]]
    try:
        results = index.fetch(ids=sample_ids, namespace="civic-content")
        for vid, vec in results.vectors.items():
            topic = vec.metadata.get("topic", "N/A") if vec.metadata else "N/A"
            logger.info(f"  ✓ {vid}: {topic}")
        logger.info(f"Found {len(results.vectors)}/{len(sample_ids)} sample vectors.")
    except Exception as e:
        logger.warning(f"Could not verify: {e}")


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if not config.PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY not set in .env")
        print("   Add your Pinecone API key to .env and try again.")
        sys.exit(1)

    logger.info(f"Connected to Pinecone index: {config.PINECONE_INDEX_NAME}")
    logger.info(f"Using embedding model: {config.EMBEDDING_MODEL}")
    logger.info(f"Content items to populate: {len(SAMPLE_CONTENT)}")

    populate(SAMPLE_CONTENT)
    list_items()
