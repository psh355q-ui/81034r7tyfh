"""
Knowledge Graph Module
======================

기업 간 관계(파트너십, 경쟁, 공급망)를 그래프 형태로 저장하고 검색

기능:
1. Triplet 저장: (Subject, Relation, Object) 형태
2. 벡터 임베딩: 의미 기반 검색 지원
3. 관계 탐색: N-hop 연결 탐색 (꼬리에 꼬리를 무는 추론)
4. 실시간 검증: 외부 검색으로 관계 유효성 확인

스키마:
    relationships (
        id SERIAL PRIMARY KEY,
        subject TEXT,           -- 주어 (예: Google)
        relation TEXT,          -- 관계 (예: partner)
        object TEXT,            -- 목적어 (예: Broadcom)
        evidence_text TEXT,     -- 증거 문장
        source TEXT,            -- 출처 URL
        date DATE,              -- 관계 확인 일자
        embedding vector(1536), -- 의미 임베딩
        confidence FLOAT,       -- 신뢰도 (0-1)
        verified_at TIMESTAMP,  -- 마지막 검증 시각
        is_active BOOLEAN       -- 관계 유효 여부
    )
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

# 선택적 임포트 - asyncpg 사용 (psycopg2/psycopg 완전 제거)
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class Relationship:
    """관계 데이터 클래스"""
    subject: str
    relation: str
    object: str
    evidence_text: Optional[str] = None
    source: Optional[str] = None
    date: Optional[datetime] = None
    confidence: float = 0.8
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_search_text(self) -> str:
        """검색용 텍스트 생성"""
        return f"{self.subject} {self.relation} {self.object}. {self.evidence_text or ''}"


class KnowledgeGraph:
    """Knowledge Graph 관리 클래스"""
    
    def __init__(
        self, 
        pg_dsn: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        embedding_dim: int = 1536
    ):
        self.pg_dsn = pg_dsn or os.getenv(
            "POSTGRES_URL",
            "postgresql://postgres:postgres@localhost:5433/knowledge_graph"
        )
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self._conn = None
        
        # 메모리 캐시 (DB 없을 때 사용)
        self._memory_cache: Dict[str, List[Relationship]] = {}
        
    # ============================================
    # Database Operations
    # ============================================
    
    async def _get_pool(self):
        """DB 연결 풀 획득 (asyncpg 사용)"""
        if not HAS_ASYNCPG:
            return None
        
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(self.pg_dsn)
            except Exception as e:
                print(f"DB Connection Failed: {e}")
                return None
        return self._pool
    
    def _get_connection(self):
        """DB 연결 획득 (Legacy - 메모리 모드 사용)"""
        # asyncpg는 비동기이므로 sync 메서드에서는 메모리 모드 사용
        return None
    
    def ensure_schema(self):
        """스키마 생성"""
        conn = self._get_connection()
        if not conn:
            print("Using in-memory mode (no database)")
            return
            
        with conn.cursor() as cur:
            # pgvector 확장
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # relationships 테이블
            cur.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id SERIAL PRIMARY KEY,
                subject TEXT NOT NULL,
                relation TEXT NOT NULL,
                object TEXT NOT NULL,
                evidence_text TEXT,
                source TEXT,
                date DATE,
                embedding vector(1536),
                confidence FLOAT DEFAULT 0.8,
                verified_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- 복합 유니크 제약
                UNIQUE(subject, relation, object)
            );
            """)
            
            # 인덱스
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_subject ON relationships(subject);
            CREATE INDEX IF NOT EXISTS idx_rel_object ON relationships(object);
            CREATE INDEX IF NOT EXISTS idx_rel_relation ON relationships(relation);
            CREATE INDEX IF NOT EXISTS idx_rel_active ON relationships(is_active);
            """)
            
            # 벡터 인덱스 (HNSW)
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_embedding 
            ON relationships 
            USING hnsw (embedding vector_cosine_ops);
            """)
            
            conn.commit()
            print("Knowledge Graph schema created successfully")
    
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
            print(f"Embedding Error: {e}")
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
        rel = Relationship(
            subject=subject,
            relation=relation,
            object=obj,
            evidence_text=evidence_text,
            source=source,
            date=datetime.now(),
            confidence=confidence
        )
        
        conn = self._get_connection()
        
        if conn:
            # DB 모드
            embedding = await self._get_embedding(rel.to_search_text())
            
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO relationships 
                    (subject, relation, object, evidence_text, source, date, 
                     embedding, confidence, verified_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (subject, relation, object) 
                DO UPDATE SET 
                    evidence_text = EXCLUDED.evidence_text,
                    source = EXCLUDED.source,
                    date = EXCLUDED.date,
                    embedding = EXCLUDED.embedding,
                    confidence = EXCLUDED.confidence,
                    verified_at = EXCLUDED.verified_at,
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
                """, (
                    subject, relation, obj, evidence_text, source,
                    datetime.now().date(), embedding, confidence, datetime.now()
                ))
                conn.commit()
                result = cur.fetchone()
                return result[0] if result else -1
        else:
            # 메모리 모드
            key = subject.lower()
            if key not in self._memory_cache:
                self._memory_cache[key] = []
            self._memory_cache[key].append(rel)
            return len(self._memory_cache[key])
    
    async def get_relationships(
        self,
        entity: str,
        relation_type: Optional[str] = None,
        direction: str = "both"  # "outgoing", "incoming", "both"
    ) -> List[Dict]:
        """엔티티의 관계 조회"""
        conn = self._get_connection()
        
        if conn:
            with conn.cursor(row_factory=dict_row) as cur:
                conditions = ["is_active = TRUE"]
                params = []
                
                if direction in ("outgoing", "both"):
                    conditions.append("subject ILIKE %s")
                    params.append(f"%{entity}%")
                    
                if direction in ("incoming", "both"):
                    if direction == "both":
                        conditions[-1] = f"(subject ILIKE %s OR object ILIKE %s)"
                        params.append(f"%{entity}%")
                    else:
                        conditions.append("object ILIKE %s")
                        params.append(f"%{entity}%")
                
                if relation_type:
                    conditions.append("relation = %s")
                    params.append(relation_type)
                
                query = f"""
                SELECT id, subject, relation, object, evidence_text, 
                       source, date, confidence, verified_at
                FROM relationships
                WHERE {' AND '.join(conditions)}
                ORDER BY confidence DESC, date DESC
                LIMIT 50;
                """
                
                cur.execute(query, params)
                return cur.fetchall()
        else:
            # 메모리 모드
            results = []
            for key, rels in self._memory_cache.items():
                for rel in rels:
                    if entity.lower() in rel.subject.lower() or \
                       entity.lower() in rel.object.lower():
                        if relation_type is None or rel.relation == relation_type:
                            results.append(rel.to_dict())
            return results
    
    async def find_path(
        self,
        start_entity: str,
        end_entity: str,
        max_depth: int = 3
    ) -> List[List[Dict]]:
        """
        두 엔티티 간 경로 탐색 (BFS)
        
        예: Google -> ? -> Nvidia 경로 찾기
        """
        conn = self._get_connection()
        if not conn:
            return []
        
        # BFS로 경로 탐색
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
            
            # 현재 엔티티의 관계 조회
            relations = await self.get_relationships(current, direction="outgoing")
            
            for rel in relations:
                new_path = path + [rel]
                
                if end_entity.lower() in rel['object'].lower():
                    paths.append(new_path)
                else:
                    queue.append((rel['object'], new_path))
        
        return paths
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """의미 기반 검색 (벡터 유사도)"""
        conn = self._get_connection()
        if not conn:
            return []
        
        embedding = await self._get_embedding(query)
        if not embedding:
            return []
        
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
            SELECT id, subject, relation, object, evidence_text,
                   source, confidence,
                   1 - (embedding <=> %s::vector) as similarity
            FROM relationships
            WHERE is_active = TRUE AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """, (embedding, embedding, limit))
            
            return cur.fetchall()
    
    # ============================================
    # Knowledge Verification
    # ============================================
    
    async def verify_relationship(
        self,
        subject: str,
        relation: str,
        obj: str,
        ai_client  # BaseAIClient
    ) -> Dict:
        """
        실시간 검색으로 관계 유효성 검증
        
        Returns:
            {
                "is_valid": True/False,
                "confidence": 0.85,
                "evidence": "...",
                "last_verified": "2025-11-26T..."
            }
        """
        # 검색 쿼리 생성
        search_query = f"{subject} {relation} {obj} partnership status 2025"
        
        # AI 클라이언트의 웹 검색 사용
        search_result = await ai_client.search_web(search_query)
        
        # 검증 프롬프트
        verify_prompt = f"""
Based on the following search results, verify if this relationship is still valid:

RELATIONSHIP: {subject} --[{relation}]--> {obj}

SEARCH RESULTS:
{search_result}

Respond in JSON format:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "evidence": "brief supporting evidence",
    "changes": "any recent changes to the relationship"
}}
"""
        
        response = await ai_client.call_api(verify_prompt, max_tokens=500)
        
        try:
            result = json.loads(response)
            result["last_verified"] = datetime.now().isoformat()
            
            # DB 업데이트
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    UPDATE relationships 
                    SET verified_at = %s,
                        confidence = %s,
                        is_active = %s
                    WHERE subject ILIKE %s 
                      AND relation = %s 
                      AND object ILIKE %s;
                    """, (
                        datetime.now(),
                        result.get("confidence", 0.8),
                        result.get("is_valid", True),
                        f"%{subject}%", relation, f"%{obj}%"
                    ))
                    conn.commit()
            
            return result
            
        except json.JSONDecodeError:
            return {
                "is_valid": True,  # 파싱 실패 시 기존 값 유지
                "confidence": 0.5,
                "evidence": response[:200],
                "last_verified": datetime.now().isoformat()
            }
    
    # ============================================
    # Seed Knowledge Import
    # ============================================
    
    async def import_seed_knowledge(self, seed_data: Dict):
        """
        초기 지식 그래프 시드 데이터 import
        
        Args:
            seed_data: config_phase14.SEED_KNOWLEDGE 형태
        """
        count = 0
        
        for entity, info in seed_data.items():
            # 파트너 관계
            for partner in info.get("partners", []):
                await self.add_relationship(
                    subject=entity,
                    relation="partner",
                    obj=partner,
                    evidence_text=info.get("notes"),
                    source="seed_knowledge",
                    confidence=0.9
                )
                count += 1
            
            # 경쟁 관계
            for competitor in info.get("competitors", []):
                await self.add_relationship(
                    subject=entity,
                    relation="competitor",
                    obj=competitor,
                    evidence_text=info.get("notes"),
                    source="seed_knowledge",
                    confidence=0.85
                )
                count += 1
            
            # 고객 관계
            for customer in info.get("customers", []):
                await self.add_relationship(
                    subject=entity,
                    relation="customer",
                    obj=customer,
                    evidence_text=info.get("notes"),
                    source="seed_knowledge",
                    confidence=0.85
                )
                count += 1
            
            # 제품 정보
            for product in info.get("products", []):
                await self.add_relationship(
                    subject=entity,
                    relation="produces",
                    obj=product,
                    evidence_text=info.get("notes"),
                    source="seed_knowledge",
                    confidence=0.95
                )
                count += 1
        
        print(f"Imported {count} relationships from seed knowledge")
        return count
    
    # ============================================
    # Statistics
    # ============================================
    
    def get_stats(self) -> Dict:
        """지식 그래프 통계"""
        conn = self._get_connection()
        
        if conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                SELECT 
                    COUNT(*) as total_relationships,
                    COUNT(DISTINCT subject) as unique_subjects,
                    COUNT(DISTINCT object) as unique_objects,
                    COUNT(*) FILTER (WHERE is_active) as active_relationships,
                    AVG(confidence) as avg_confidence
                FROM relationships;
                """)
                stats = cur.fetchone()
                
                cur.execute("""
                SELECT relation, COUNT(*) as count
                FROM relationships
                WHERE is_active = TRUE
                GROUP BY relation
                ORDER BY count DESC;
                """)
                relation_counts = cur.fetchall()
                
                stats["relation_distribution"] = relation_counts
                return dict(stats)
        else:
            total = sum(len(rels) for rels in self._memory_cache.values())
            return {
                "total_relationships": total,
                "unique_subjects": len(self._memory_cache),
                "mode": "in-memory"
            }


# ============================================
# Helper Functions
# ============================================

async def create_knowledge_graph() -> KnowledgeGraph:
    """Knowledge Graph 인스턴스 생성 및 초기화"""
    kg = KnowledgeGraph()
    kg.ensure_schema()
    return kg


async def demo():
    """데모 실행"""
    print("=== Knowledge Graph Demo ===\n")
    
    kg = await create_knowledge_graph()
    
    # Seed 데이터 import
    from backend.config_phase14 import SEED_KNOWLEDGE
    await kg.import_seed_knowledge(SEED_KNOWLEDGE)
    
    # 관계 조회
    print("\n=== Google's Relationships ===")
    relations = await kg.get_relationships("Google")
    for rel in relations[:5]:
        print(f"  {rel['subject']} --[{rel['relation']}]--> {rel['object']}")
    
    # 경로 탐색
    print("\n=== Path: Google -> Nvidia ===")
    paths = await kg.find_path("Google", "Nvidia", max_depth=2)
    for i, path in enumerate(paths, 1):
        print(f"  Path {i}:")
        for step in path:
            print(f"    {step['subject']} --[{step['relation']}]--> {step['object']}")
    
    # 통계
    print("\n=== Statistics ===")
    stats = kg.get_stats()
    print(f"  Total Relationships: {stats.get('total_relationships', 0)}")
    print(f"  Unique Subjects: {stats.get('unique_subjects', 0)}")


if __name__ == "__main__":
    asyncio.run(demo())
