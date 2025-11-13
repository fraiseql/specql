"""Backfill embeddings for existing patterns"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import psycopg
from psycopg.types.json import Jsonb
from src.infrastructure.services.embedding_service import get_embedding_service
from src.core.config import get_config


def backfill_embeddings():
    """Generate and store embeddings for all patterns without embeddings"""
    config = get_config()
    if not config.database_url:
        raise ValueError("SPECQL_DB_URL environment variable not set")

    embedding_service = get_embedding_service()

    print("🔄 Starting embedding backfill...")
    print(f"📊 Using model: {embedding_service.model_name}")
    print(f"📐 Embedding dimension: {embedding_service.embedding_dimension}")

    with psycopg.connect(config.database_url) as conn:
        with conn.cursor() as cur:
            # Get patterns without embeddings
            cur.execute("""
                SELECT id, name, description, implementation, category
                FROM pattern_library.domain_patterns
                WHERE embedding IS NULL
                ORDER BY id
            """)

            patterns = cur.fetchall()
            total = len(patterns)

            if total == 0:
                print("✅ All patterns already have embeddings")
                return

            print(f"📝 Found {total} patterns without embeddings")
            print()

            # Process each pattern
            for i, (pattern_id, name, description, implementation, category) in enumerate(patterns, 1):
                print(f"[{i}/{total}] Processing: {name}")

                # Generate embedding
                try:
                    embedding = embedding_service.create_pattern_embedding(
                        pattern_name=name,
                        description=description or "",
                        implementation=implementation or "",
                        category=category or ""
                    )

                    # Convert to list for PostgreSQL
                    embedding_list = embedding_service.embedding_to_list(embedding)

                    # Update pattern
                    cur.execute("""
                        UPDATE pattern_library.domain_patterns
                        SET embedding = %s
                        WHERE id = %s
                    """, (embedding_list, pattern_id))

                    print(f"   ✅ Generated embedding (dim={len(embedding_list)})")

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue

            # Commit all updates
            conn.commit()

            print()
            print(f"✅ Backfill complete! Updated {total} patterns")

            # Verify
            cur.execute("""
                SELECT COUNT(*)
                FROM pattern_library.domain_patterns
                WHERE embedding IS NOT NULL
            """)
            result = cur.fetchone()
            embedded_count = result[0] if result else 0

            print(f"📊 Total patterns with embeddings: {embedded_count}")


def verify_embeddings():
    """Verify embedding quality with sample similarity search"""
    config = get_config()
    if not config.database_url:
        raise ValueError("SPECQL_DB_URL environment variable not set")

    print()
    print("🔍 Verifying embeddings with sample search...")

    with psycopg.connect(config.database_url) as conn:
        with conn.cursor() as cur:
            # Sample query: find patterns similar to "email validation"
            embedding_service = get_embedding_service()
            query_embedding = embedding_service.generate_embedding("email validation")
            query_list = embedding_service.embedding_to_list(query_embedding)

            cur.execute("""
                SELECT
                    name,
                    description,
                    1 - (embedding <=> %s::vector) as similarity
                FROM pattern_library.domain_patterns
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 5
            """, (query_list, query_list))

            results = cur.fetchall()

            print()
            print("Top 5 matches for 'email validation':")
            for name, description, similarity in results:
                print(f"  • {name} (similarity: {similarity:.3f})")
                print(f"    {description[:80]}...")
                print()


if __name__ == "__main__":
    try:
        backfill_embeddings()
        verify_embeddings()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)