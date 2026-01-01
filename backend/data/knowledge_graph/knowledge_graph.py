"""
Knowledge Graph Module
======================

기업 간 관계(파트너십, 경쟁, 공급망)를 그래프 형태로 저장하고 검색

기능:
1. Triplet 저장: (Subject, Relation, Object) 형태
2. 벡터 임베딩: 의미 기반 검색 지원
3. 관계 탐색: N-hop 연결 탐색
4. 실시간 검증: 외부 검색으로 관계 유효성 확인

스키마:
    backend.database.models.Relationship 참조
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_, func
from pgvector.sqlalchemy import Vector

from backend.database.models import Relationship
from backend.database.repository import get_sync_session

# Optional: OpenAI
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Knowledge Graph 관리 클래스 (SQLAlchemy Version)"""
    
    def __init__(
        self, 
        db: Session = None,
        embedding_model: str = "text-embedding-3-small",
        embedding_dim: int = 1536
    ):
        self.db = db if db else get_sync_session()
        self._owned_session = db is None
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        
    def __del__(self):
        if hasattr(self, '_owned_session') and self._owned_session:
            self.db.close()
            
    # ============================================
    # Embedding
    # ============================================
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """텍스트 임베딩 생성"""
        if not HAS_OPENAI:
            return None
            
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
            
        try:
            client = AsyncOpenAI(api_key=api_key)
            response = await client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding Error: {e}")
            return None
    
    # ============================================
    # CRUD Operations
    # ============================================
    
    async def add_relationship(
        self,
        subject: str,
        relation: str,
        obj: str,
        evidence_text: Optional[str] = None,
        source: Optional[str] = None,
        confidence: float = 0.8
    ) -> int:
        """관계 추가 (Upsert)"""
        try:
            # Check existence
            existing = self.db.query(Relationship).filter(
                and_(
                    Relationship.subject == subject,
                    Relationship.relation == relation,
                    Relationship.object == obj
                )
            ).first()

            search_text = f"{subject} {relation} {obj}. {evidence_text or ''}"
            embedding = await self._get_embedding(search_text)

            if existing:
                # Update
                existing.evidence_text = evidence_text
                existing.source = source
                existing.date = datetime.now()
                if embedding:
                    existing.embedding = embedding
                existing.confidence = confidence
                existing.is_active = True
                existing.updated_at = datetime.now()

                self.db.commit()
                self.db.refresh(existing)
                return existing.id
            else:
                # Insert
                rel = Relationship(
                    subject=subject,
                    relation=relation,
                    object=obj,
                    evidence_text=evidence_text,
                    source=source,
                    date=datetime.now(),
                    embedding=embedding,
                    confidence=confidence,
                    is_active=True
                )
                self.db.add(rel)
                self.db.commit()
                self.db.refresh(rel)
                return rel.id
        except Exception as e:
            logger.warning(f"⚠️ relationships 테이블이 없어서 관계 추가 실패 (정상 동작): {e}")
            return -1
    
    async def get_relationships(
        self,
        entity: str,
        relation_type: Optional[str] = None,
        direction: str = "both"  # "outgoing", "incoming", "both"
    ) -> List[Dict]:
        """엔티티의 관계 조회"""
        try:
            query = self.db.query(Relationship).filter(Relationship.is_active == True)

            conditions = []
            if direction == "outgoing":
                conditions.append(Relationship.subject.ilike(f"%{entity}%"))
            elif direction == "incoming":
                conditions.append(Relationship.object.ilike(f"%{entity}%"))
            else: # both
                conditions.append(or_(
                    Relationship.subject.ilike(f"%{entity}%"),
                    Relationship.object.ilike(f"%{entity}%")
                ))

            if conditions:
                query = query.filter(or_(*conditions) if len(conditions) > 1 else conditions[0])

            if relation_type:
                query = query.filter(Relationship.relation == relation_type)

            results = query.order_by(Relationship.confidence.desc(), Relationship.date.desc()).limit(50).all()

            return [
                {
                    "id": r.id,
                    "subject": r.subject,
                    "relation": r.relation,
                    "object": r.object,
                    "evidence_text": r.evidence_text,
                    "source": r.source,
                    "date": r.date,
                    "confidence": r.confidence,
                    "verified_at": r.verified_at
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"⚠️ relationships 테이블이 없거나 조회 실패 (정상 동작): {e}")
            return []
    
    async def find_path(
        self,
        start_entity: str,
        end_entity: str,
        max_depth: int = 3
    ) -> List[List[Dict]]:
        """두 엔티티 간 경로 탐색 (BFS)"""
        try:
            # BFS (Client-side logic with repeated DB queries - simpler implementation)
            visited = set()
            queue = [(start_entity, [])]
            paths = []

            while queue and len(paths) < 5:
                current, path = queue.pop(0)

                if len(path) >= max_depth:
                    continue

                if current.lower() in visited:
                    continue
                visited.add(current.lower())

                # Outgoing queries
                # Using simple query, not async
                rels = self.db.query(Relationship).filter(
                    and_(
                        Relationship.subject.ilike(f"%{current}%"),
                        Relationship.is_active == True
                    )
                ).all()

                for rel in rels:
                    # Convert to dict
                    rel_dict = {
                        "id": rel.id,
                        "subject": rel.subject,
                        "relation": rel.relation,
                        "object": rel.object
                    }

                    new_path = path + [rel_dict]

                    if end_entity.lower() in rel.object.lower():
                        paths.append(new_path)
                    else:
                        queue.append((rel.object, new_path))

            return paths
        except Exception as e:
            logger.warning(f"⚠️ relationships 테이블이 없어서 경로 탐색 실패 (정상 동작): {e}")
            return []
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """의미 기반 검색 (벡터 유사도)"""
        try:
            embedding = await self._get_embedding(query)
            if not embedding:
                return []

            # pgvector cosine distance: <=> operator
            # SQLAlchemy stores embedding as Vector

            results = self.db.query(
                Relationship,
                Relationship.embedding.cosine_distance(embedding).label("distance")
            ).filter(
                Relationship.is_active == True,
                Relationship.embedding.isnot(None)
            ).order_by(
                "distance"
            ).limit(limit).all()

            return [
                {
                    "id": r[0].id,
                    "subject": r[0].subject,
                    "relation": r[0].relation,
                    "object": r[0].object,
                    "evidence_text": r[0].evidence_text,
                    "confidence": r[0].confidence,
                    "similarity": 1 - r[1]
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"⚠️ relationships 테이블이 없어서 의미 검색 실패 (정상 동작): {e}")
            return []
    
    # ============================================
    # Knowledge Verification
    # ============================================
    
    async def verify_relationship(
        self,
        subject: str,
        relation: str,
        obj: str,
        ai_client
    ) -> Dict:
        """실시간 검색으로 관계 유효성 검증"""
        search_query = f"{subject} {relation} {obj} partnership status 2025"
        search_result = await ai_client.search_web(search_query)
        
        verify_prompt = f"""
Based on the following search results, verify if this relationship is still valid:
RELATIONSHIP: {subject} --[{relation}]--> {obj}
SEARCH RESULTS:
{search_result}
Respond in JSON format:
{{ "is_valid": true/false, "confidence": 0.0-1.0, "evidence": "brief", "changes": "..." }}
"""
        response = await ai_client.call_api(verify_prompt, max_tokens=500)
        
        try:
            result = json.loads(response)
            result["last_verified"] = datetime.now().isoformat()
            
            # Update DB
            rels = self.db.query(Relationship).filter(
                and_(
                    Relationship.subject.ilike(f"%{subject}%"),
                    Relationship.relation == relation,
                    Relationship.object.ilike(f"%{obj}%")
                )
            ).all()
            
            for rel in rels:
                rel.verified_at = datetime.now()
                rel.confidence = result.get("confidence", 0.8)
                rel.is_active = result.get("is_valid", True)
            
            self.db.commit()
            return result
        except:
            return {"is_valid": True, "error": "Parse failed"}

    # ============================================
    # Seed Knowledge Import
    # ============================================
    
    async def import_seed_knowledge(self, seed_data: Dict):
        """초기 지식 그래프 시드 데이터 import"""
        count = 0
        for entity, info in seed_data.items():
            # Partners
            for partner in info.get("partners", []):
                await self.add_relationship(entity, "partner", partner, info.get("notes"), "seed", 0.9)
                count += 1
            # Competitors
            for comp in info.get("competitors", []):
                await self.add_relationship(entity, "competitor", comp, info.get("notes"), "seed", 0.85)
                count += 1
            # Products
            for prod in info.get("products", []):
                await self.add_relationship(entity, "produces", prod, info.get("notes"), "seed", 0.95)
                count += 1
        print(f"Imported {count} relationships")
        return count
    
    # ============================================
    # Statistics
    # ============================================
    
    def get_stats(self) -> Dict:
        """지식 그래프 통계"""
        total = self.db.query(func.count(Relationship.id)).scalar()
        active = self.db.query(func.count(Relationship.id)).filter(Relationship.is_active == True).scalar()
        subjects = self.db.query(func.count(func.distinct(Relationship.subject))).scalar()
        
        return {
            "total_relationships": total,
            "active_relationships": active,
            "unique_subjects": subjects
        }


# ============================================
# Helper Functions
# ============================================

async def create_knowledge_graph() -> KnowledgeGraph:
    """Knowledge Graph 인스턴스 생성"""
    return KnowledgeGraph()


async def demo():
    """데모 실행"""
    print("=== Knowledge Graph Demo (SQLAlchemy) ===\n")
    
    kg = await create_knowledge_graph()
    
    # Check if seed module exists, otherwise skip import test
    try:
        from backend.config_phase14 import SEED_KNOWLEDGE
        await kg.import_seed_knowledge(SEED_KNOWLEDGE)
    except ImportError:
        print("SEED_KNOWLEDGE not found, skipping import.")
    
    # Relation query
    print("\n=== Relations ===")
    relations = await kg.get_relationships("Google")
    for r in relations[:3]:
        print(f"  {r['subject']} -> {r['relation']} -> {r['object']}")
        
    # Stats
    print("\n=== Stats ===")
    print(kg.get_stats())


if __name__ == "__main__":
    asyncio.run(demo())
