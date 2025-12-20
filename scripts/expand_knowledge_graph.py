"""
Expand Knowledge Graph to 100+ Relationships

Adds comprehensive AI ecosystem relationships:
- Cloud providers & AI infrastructure
- Semiconductor supply chain
- Memory & storage
- Networking
- Power & cooling
- Software platforms
- Edge AI devices
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.data.knowledge_graph.knowledge_graph import KnowledgeGraph


# Expanded Knowledge Base (100+ relationships)
EXPANDED_KNOWLEDGE = {
    # ============================================
    # Cloud Providers & AI Infrastructure (20)
    # ============================================
    "Microsoft": [
        ("partners", "OpenAI", 0.95, "Strategic partnership & $13B investment"),
        ("partners", "CoreWeave", 0.80, "GPU cloud infrastructure provider"),
        ("partners", "Nvidia", 0.90, "H100/H200 GPU purchase agreements"),
        ("invests_in", "OpenAI", 0.95, "$13B investment across multiple rounds"),
        ("competes_with", "Google", 0.85, "Cloud AI market competition"),
        ("competes_with", "AWS", 0.85, "Azure vs AWS infrastructure"),
        ("suppliers", "Intel", 0.70, "Azure datacenter CPUs"),
        ("suppliers", "AMD", 0.75, "MI300 AI accelerators for Azure"),
    ],

    "Google": [
        ("partners", "Broadcom", 0.90, "TPU chip design partnership"),
        ("partners", "Nvidia", 0.70, "GPU purchase for Cloud"),
        ("competes_with", "Microsoft", 0.85, "Cloud AI market"),
        ("competes_with", "AWS", 0.85, "GCP vs AWS"),
        ("suppliers", "TSMC", 0.80, "TPU manufacturing"),
        ("suppliers", "SK Hynix", 0.75, "HBM memory for TPUs"),
        ("invests_in", "Anthropic", 0.80, "$2B investment in AI research"),
    ],

    "AWS": [
        ("partners", "Nvidia", 0.90, "P5 instances with H100 GPUs"),
        ("partners", "Marvell", 0.85, "Custom networking chips"),
        ("partners", "AMD", 0.80, "EC2 instances with EPYC"),
        ("competes_with", "Microsoft", 0.85, "Azure competition"),
        ("competes_with", "Google", 0.85, "GCP competition"),
        ("suppliers", "Arista", 0.80, "Datacenter networking"),
        ("suppliers", "Vertiv", 0.70, "Power & cooling infrastructure"),
    ],

    "CoreWeave": [
        ("partners", "Microsoft", 0.80, "AI training infrastructure"),
        ("partners", "Nvidia", 0.95, "Primary GPU cloud provider"),
        ("suppliers", "Super Micro Computer", 0.85, "GPU server infrastructure"),
    ],

    "OpenAI": [
        ("partners", "Microsoft", 0.95, "Exclusive cloud partnership"),
        ("partners", "Nvidia", 0.90, "Training infrastructure"),
        ("competes_with", "Anthropic", 0.75, "LLM market"),
        ("competes_with", "Google", 0.75, "AI research & products"),
    ],

    "Anthropic": [
        ("partners", "Google", 0.80, "$2B investment"),
        ("partners", "AWS", 0.75, "Cloud partnership"),
        ("competes_with", "OpenAI", 0.75, "LLM market"),
    ],

    # ============================================
    # Semiconductor Foundries & Designers (25)
    # ============================================
    "Nvidia": [
        ("partners", "Microsoft", 0.90, "H100/H200 supply deals"),
        ("partners", "AWS", 0.90, "P5 instances"),
        ("partners", "Google", 0.70, "GPU sales"),
        ("partners", "Meta", 0.85, "AI infrastructure"),
        ("suppliers", "TSMC", 0.95, "GPU manufacturing at 4nm/5nm"),
        ("suppliers", "SK Hynix", 0.90, "HBM3E memory"),
        ("suppliers", "Micron", 0.70, "HBM alternative supply"),
        ("competes_with", "AMD", 0.90, "AI accelerator market"),
        ("competes_with", "Intel", 0.75, "GPU market"),
    ],

    "AMD": [
        ("partners", "Microsoft", 0.75, "MI300 for Azure"),
        ("partners", "AWS", 0.80, "EPYC CPUs"),
        ("partners", "Meta", 0.70, "MI300 deployment"),
        ("suppliers", "TSMC", 0.95, "MI300 & EPYC manufacturing"),
        ("suppliers", "SK Hynix", 0.85, "HBM3E for MI300"),
        ("competes_with", "Nvidia", 0.90, "AI GPU market"),
        ("competes_with", "Intel", 0.85, "CPU market"),
    ],

    "Intel": [
        ("partners", "Microsoft", 0.70, "Xeon CPUs for Azure"),
        ("partners", "AWS", 0.70, "EC2 instances"),
        ("competes_with", "AMD", 0.85, "CPU market"),
        ("competes_with", "Nvidia", 0.75, "GPU & AI accelerators"),
        ("competes_with", "TSMC", 0.60, "Foundry services"),
    ],

    "Broadcom": [
        ("partners", "Google", 0.90, "TPU ASIC design"),
        ("partners", "Apple", 0.85, "iPhone components"),
        ("partners", "Meta", 0.75, "Custom AI chips"),
        ("suppliers", "TSMC", 0.80, "Chip manufacturing"),
    ],

    "TSMC": [
        ("partners", "Nvidia", 0.95, "Primary foundry for GPUs"),
        ("partners", "AMD", 0.95, "MI300 & Ryzen manufacturing"),
        ("partners", "Apple", 0.95, "A-series & M-series chips"),
        ("partners", "Broadcom", 0.80, "ASIC manufacturing"),
        ("partners", "Google", 0.80, "TPU manufacturing"),
        ("suppliers", "ASML", 0.95, "EUV lithography equipment"),
        ("competes_with", "Samsung", 0.85, "Foundry market"),
        ("competes_with", "Intel", 0.60, "Foundry services"),
    ],

    "Samsung": [
        ("competes_with", "TSMC", 0.85, "Foundry market"),
        ("competes_with", "SK Hynix", 0.90, "Memory market"),
        ("competes_with", "Micron", 0.80, "DRAM & NAND"),
    ],

    "ASML": [
        ("partners", "TSMC", 0.95, "EUV equipment supplier"),
        ("partners", "Samsung", 0.85, "EUV equipment"),
        ("partners", "Intel", 0.80, "EUV for Intel foundries"),
    ],

    # ============================================
    # Memory & Storage (15)
    # ============================================
    "SK Hynix": [
        ("partners", "Nvidia", 0.90, "HBM3E for H100/H200"),
        ("partners", "AMD", 0.85, "HBM3E for MI300"),
        ("partners", "Google", 0.75, "HBM for TPUs"),
        ("competes_with", "Samsung", 0.90, "Memory market"),
        ("competes_with", "Micron", 0.85, "DRAM market"),
    ],

    "Micron": [
        ("partners", "Nvidia", 0.70, "HBM alternative supplier"),
        ("partners", "AMD", 0.70, "Memory supply"),
        ("partners", "Intel", 0.75, "Memory for CPUs"),
        ("competes_with", "SK Hynix", 0.85, "DRAM market"),
        ("competes_with", "Samsung", 0.80, "Memory market"),
    ],

    # ============================================
    # Networking & Interconnect (10)
    # ============================================
    "Arista": [
        ("partners", "Microsoft", 0.85, "Azure datacenter networking"),
        ("partners", "Meta", 0.90, "Meta AI cluster networking"),
        ("partners", "AWS", 0.80, "EC2 networking"),
        ("competes_with", "Cisco", 0.75, "Datacenter switches"),
    ],

    "Marvell": [
        ("partners", "AWS", 0.85, "Custom networking chips"),
        ("partners", "Microsoft", 0.70, "Azure networking"),
        ("competes_with", "Broadcom", 0.70, "Networking chips"),
    ],

    "Cisco": [
        ("competes_with", "Arista", 0.75, "Datacenter networking"),
        ("partners", "Nvidia", 0.60, "AI networking solutions"),
    ],

    # ============================================
    # Server & Infrastructure (8)
    # ============================================
    "Super Micro Computer": [
        ("partners", "Nvidia", 0.90, "GPU server solutions"),
        ("partners", "CoreWeave", 0.85, "GPU cloud infrastructure"),
        ("partners", "Microsoft", 0.70, "Azure servers"),
        ("competes_with", "Dell", 0.75, "Server market"),
    ],

    "Dell": [
        ("partners", "Nvidia", 0.85, "PowerEdge GPU servers"),
        ("partners", "AMD", 0.75, "EPYC server solutions"),
        ("competes_with", "Super Micro Computer", 0.75, "GPU servers"),
    ],

    "Vertiv": [
        ("partners", "AWS", 0.70, "Datacenter power & cooling"),
        ("partners", "Microsoft", 0.70, "Azure infrastructure"),
    ],

    # ============================================
    # Edge AI & Devices (10)
    # ============================================
    "Apple": [
        ("partners", "TSMC", 0.95, "M-series & A-series manufacturing"),
        ("partners", "Broadcom", 0.85, "iPhone components"),
        ("suppliers", "Qualcomm", 0.70, "Modem chips (transitioning away)"),
        ("competes_with", "Google", 0.75, "Smartphone AI"),
        ("competes_with", "Samsung", 0.85, "Smartphone market"),
    ],

    "Qualcomm": [
        ("partners", "Microsoft", 0.75, "ARM Windows devices"),
        ("partners", "Meta", 0.70, "VR/AR chipsets"),
        ("suppliers", "TSMC", 0.85, "Snapdragon manufacturing"),
        ("competes_with", "Apple", 0.80, "Mobile AI chips"),
        ("competes_with", "MediaTek", 0.75, "Mobile SoCs"),
    ],

    "MediaTek": [
        ("competes_with", "Qualcomm", 0.75, "Mobile chipsets"),
        ("suppliers", "TSMC", 0.80, "SoC manufacturing"),
    ],

    # ============================================
    # Automotive & Autonomous Driving (8)
    # ============================================
    "Tesla": [
        ("partners", "Luminar", 0.85, "LiDAR sensors"),
        ("partners", "Nvidia", 0.60, "FSD training infrastructure"),
        ("competes_with", "Mobileye", 0.70, "Autonomous driving"),
    ],

    "Luminar": [
        ("partners", "Tesla", 0.85, "Next-gen LiDAR"),
        ("partners", "Volvo", 0.80, "Production vehicles"),
        ("suppliers", "ON Semiconductor", 0.80, "LiDAR components"),
        ("competes_with", "Innoviz", 0.80, "LiDAR market"),
    ],

    "Innoviz": [
        ("competes_with", "Luminar", 0.80, "LiDAR market"),
    ],

    "Mobileye": [
        ("partners", "Intel", 0.90, "Subsidiary relationship"),
        ("competes_with", "Tesla", 0.70, "Autonomous driving"),
        ("competes_with", "Nvidia", 0.75, "ADAS market"),
    ],

    "ON Semiconductor": [
        ("partners", "Luminar", 0.80, "LiDAR components"),
        ("partners", "Tesla", 0.70, "Automotive sensors"),
    ],

    # ============================================
    # Software & Platforms (6)
    # ============================================
    "Meta": [
        ("partners", "Nvidia", 0.85, "AI training infrastructure"),
        ("partners", "AMD", 0.70, "MI300 deployment"),
        ("partners", "Arista", 0.90, "Datacenter networking"),
        ("competes_with", "Microsoft", 0.60, "LLaMA vs OpenAI"),
        ("competes_with", "Google", 0.65, "AI research"),
    ],
}


async def import_expanded_knowledge(kg: KnowledgeGraph, data: dict) -> int:
    """Import knowledge in tuple format: (relation_type, object, confidence, notes)"""
    count = 0

    for subject, relations in data.items():
        for relation_type, obj, confidence, notes in relations:
            await kg.add_relationship(
                subject=subject,
                relation=relation_type,
                obj=obj,
                evidence_text=notes,
                source="expanded_knowledge",
                confidence=confidence
            )
            count += 1

    return count


async def main():
    print("=" * 80)
    print("Expanding Knowledge Graph to 100+ Relationships")
    print("=" * 80)

    # Initialize Knowledge Graph
    kg = KnowledgeGraph()

    # Count total relationships
    total_relations = sum(len(relations) for relations in EXPANDED_KNOWLEDGE.values())
    print(f"\nTotal relationships to add: {total_relations}")

    # Import expanded knowledge
    print("\n[IMPORTING] Adding relationships to Knowledge Graph...")
    count = await import_expanded_knowledge(kg, EXPANDED_KNOWLEDGE)
    print(f"[SUCCESS] Imported {count} relationships")

    # Get statistics
    stats = kg.get_stats()
    print("\n" + "=" * 80)
    print("KNOWLEDGE GRAPH STATISTICS")
    print("=" * 80)
    print(f"  Total Relationships: {stats['total_relationships']}")
    print(f"  Unique Subjects: {stats['unique_subjects']}")
    print(f"  Unique Objects: {stats['unique_objects']}")
    print(f"  Average Confidence: {stats['avg_confidence']:.2f}")

    # Test queries
    print("\n" + "=" * 80)
    print("SAMPLE QUERIES")
    print("=" * 80)

    # Query 1: Microsoft's partners
    print("\n[QUERY 1] Microsoft's partners:")
    ms_partners = await kg.get_relationships("Microsoft", relationship_type="partners")
    for rel in ms_partners[:5]:
        print(f"  - {rel['object']}: {rel['notes']} (confidence: {rel['confidence']:.0%})")

    # Query 2: Nvidia's supply chain
    print("\n[QUERY 2] Nvidia's suppliers:")
    nvda_suppliers = await kg.get_relationships("Nvidia", relationship_type="suppliers")
    for rel in nvda_suppliers:
        print(f"  - {rel['object']}: {rel['notes']} (confidence: {rel['confidence']:.0%})")

    # Query 3: Find path from Microsoft to Nvidia
    print("\n[QUERY 3] Path from Microsoft to Nvidia:")
    paths = await kg.find_path("Microsoft", "Nvidia", max_depth=3)
    if paths:
        path = paths[0]
        path_str = " -> ".join(path)
        print(f"  {path_str}")

    # Query 4: Find path from Amazon to TSMC
    print("\n[QUERY 4] Path from AWS to TSMC:")
    paths = await kg.find_path("AWS", "TSMC", max_depth=3)
    if paths:
        path = paths[0]
        path_str = " -> ".join(path)
        print(f"  {path_str}")

    print("\n" + "=" * 80)
    print("Knowledge Graph Expansion Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
