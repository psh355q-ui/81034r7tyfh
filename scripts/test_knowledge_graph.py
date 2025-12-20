"""
Test Knowledge Graph with pgvector

Phase 14 Option B: Knowledge Graph + pgvector 통합 테스트
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph
from backend.config_phase14 import SEED_KNOWLEDGE


async def main():
    print("=" * 80)
    print("Phase 14 Option B: Knowledge Graph + pgvector Integration Test")
    print("=" * 80)

    # Knowledge Graph 생성
    kg = KnowledgeGraph()
    kg.ensure_schema()

    print("\n[TEST 1] Importing Seed Knowledge...")
    count = await kg.import_seed_knowledge(SEED_KNOWLEDGE)
    print(f"[SUCCESS] Imported {count} relationships")

    print("\n[TEST 2] Query Google's Relationships...")
    relations = await kg.get_relationships("Google")
    print(f"[SUCCESS] Found {len(relations)} relationships for Google:")
    for rel in relations[:5]:
        print(f"  - {rel['subject']} --[{rel['relation']}]--> {rel['object']}")

    print("\n[TEST 3] Find Path: Google -> Nvidia...")
    paths = await kg.find_path("Google", "Nvidia", max_depth=3)
    print(f"[SUCCESS] Found {len(paths)} paths:")
    for i, path in enumerate(paths[:3], 1):
        print(f"  Path {i}:")
        for step in path:
            print(f"    {step['subject']} --[{step['relation']}]--> {step['object']}")

    print("\n[TEST 4] Knowledge Graph Statistics...")
    stats = kg.get_stats()
    print("[SUCCESS] Statistics:")
    print(f"  - Total Relationships: {stats.get('total_relationships', 0)}")
    print(f"  - Active Relationships: {stats.get('active_relationships', 0)}")
    print(f"  - Unique Subjects: {stats.get('unique_subjects', 0)}")
    print(f"  - Unique Objects: {stats.get('unique_objects', 0)}")
    print(f"  - Average Confidence: {stats.get('avg_confidence', 0):.2f}")

    if 'relation_distribution' in stats:
        print("\n  Relation Distribution:")
        for rel_stat in stats['relation_distribution'][:5]:
            print(f"    - {rel_stat['relation']}: {rel_stat['count']}")

    print("\n[TEST 5] Semantic Search (if OpenAI API available)...")
    try:
        results = await kg.semantic_search("AI chip partnerships", limit=5)
        if results:
            print(f"[SUCCESS] Found {len(results)} semantically similar relationships:")
            for res in results:
                similarity = res.get('similarity', 0)
                print(f"  - {res['subject']} --[{res['relation']}]--> {res['object']} (similarity: {similarity:.2f})")
        else:
            print("[INFO] Semantic search requires OpenAI API key and embeddings")
    except Exception as e:
        print(f"[INFO] Semantic search skipped: {e}")

    print("\n" + "=" * 80)
    print("All Knowledge Graph tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
