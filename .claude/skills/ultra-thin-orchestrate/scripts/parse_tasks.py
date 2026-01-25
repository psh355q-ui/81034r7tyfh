#!/usr/bin/env python3
"""
TASKS.md 파서 - Ultra-Thin Orchestrate용

TASKS.md 파일을 파싱하여 최소한의 태스크 정보만 추출합니다.
컨텍스트 절약을 위해 태스크 상세 설명은 포함하지 않습니다.

사용법:
    python parse_tasks.py --input docs/planning/TASKS.md --output .claude/parsed_tasks.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


def parse_tasks_md(content: str) -> dict:
    """
    TASKS.md 내용을 파싱하여 Ultra-Thin 형식으로 변환

    Returns:
        {
            "project": "프로젝트명",
            "total_tasks": 75,
            "phases": [0, 1, 2, 3],
            "tasks": {
                "T0.1": {"phase": 0, "status": "completed", "depends_on": [], "parallel_with": []},
                "T1.1": {"phase": 1, "status": "pending", "depends_on": ["T0.5.1"], "parallel_with": ["T1.2"]},
                ...
            }
        }
    """
    result = {
        "project": "",
        "total_tasks": 0,
        "phases": [],
        "tasks": {}
    }

    # 프로젝트명 추출 (첫 번째 # 헤더)
    project_match = re.search(r'^#\s+(?:TASKS:\s*)?(.+?)(?:\s*-|$)', content, re.MULTILINE)
    if project_match:
        result["project"] = project_match.group(1).strip()

    # 태스크 패턴들
    # 형식 1: ### [ ] Phase 1, T1.1: 태스크명
    # 형식 2: ### [x] Phase 0, T0.1: 태스크명
    # 형식 3: [ ] T1.1: 태스크명
    task_pattern = re.compile(
        r'(?:###\s*)?\[([x\s])\]\s*(?:Phase\s*(\d+),?\s*)?'
        r'(T\d+(?:\.\d+)?(?:\.\d+)?)\s*:\s*(.+?)(?:\n|$)',
        re.IGNORECASE
    )

    # 의존성 패턴
    depends_pattern = re.compile(r'(?:의존|depends?|의존성)[\s:]*\[?([T\d.,\s]+)\]?', re.IGNORECASE)

    # 병렬 실행 패턴
    parallel_pattern = re.compile(r'(?:병렬|parallel|병렬\s*실행|parallel_with)[\s:]*\[?([T\d.,\s]+)\]?', re.IGNORECASE)

    # 담당자 패턴
    specialist_pattern = re.compile(r'(?:담당|specialist|agent)[\s:]*([a-zA-Z-]+(?:-specialist)?)', re.IGNORECASE)

    phases_set = set()

    # 태스크 블록 단위로 파싱
    lines = content.split('\n')
    current_task = None
    current_block = []

    for line in lines:
        task_match = task_pattern.search(line)

        if task_match:
            # 이전 태스크 블록 처리
            if current_task and current_block:
                _process_task_block(result["tasks"], current_task, current_block,
                                   depends_pattern, parallel_pattern, specialist_pattern)

            # 새 태스크 시작
            status_char = task_match.group(1)
            phase_num = int(task_match.group(2)) if task_match.group(2) else 0
            task_id = task_match.group(3)

            status = "completed" if status_char.lower() == 'x' else "pending"

            current_task = task_id
            current_block = [line]

            result["tasks"][task_id] = {
                "phase": phase_num,
                "status": status,
                "depends_on": [],
                "parallel_with": [],
                "specialist": "general-purpose"
            }

            phases_set.add(phase_num)
        elif current_task:
            current_block.append(line)

    # 마지막 태스크 처리
    if current_task and current_block:
        _process_task_block(result["tasks"], current_task, current_block,
                           depends_pattern, parallel_pattern, specialist_pattern)

    result["phases"] = sorted(list(phases_set))
    result["total_tasks"] = len(result["tasks"])

    return result


def _process_task_block(tasks: dict, task_id: str, block: list,
                        depends_pattern, parallel_pattern, specialist_pattern):
    """태스크 블록에서 의존성, 병렬 실행, 담당자 정보 추출"""
    block_text = '\n'.join(block)

    # 의존성 추출
    depends_match = depends_pattern.search(block_text)
    if depends_match:
        deps = re.findall(r'T\d+(?:\.\d+)?(?:\.\d+)?', depends_match.group(1))
        tasks[task_id]["depends_on"] = deps

    # 병렬 실행 추출
    parallel_match = parallel_pattern.search(block_text)
    if parallel_match:
        parallels = re.findall(r'T\d+(?:\.\d+)?(?:\.\d+)?', parallel_match.group(1))
        tasks[task_id]["parallel_with"] = parallels

    # 담당자 추출
    specialist_match = specialist_pattern.search(block_text)
    if specialist_match:
        tasks[task_id]["specialist"] = specialist_match.group(1)


def detect_circular_dependencies(tasks: dict) -> Optional[list]:
    """
    순환 의존성 검출

    Returns:
        순환 경로 리스트 또는 None (순환 없음)
    """
    def dfs(task_id: str, path: list, visited: set, rec_stack: set) -> Optional[list]:
        visited.add(task_id)
        rec_stack.add(task_id)
        path.append(task_id)

        for dep in tasks.get(task_id, {}).get("depends_on", []):
            if dep not in tasks:
                continue  # 존재하지 않는 태스크는 무시
            if dep not in visited:
                result = dfs(dep, path, visited, rec_stack)
                if result:
                    return result
            elif dep in rec_stack:
                # 순환 발견
                cycle_start = path.index(dep)
                return path[cycle_start:] + [dep]

        path.pop()
        rec_stack.remove(task_id)
        return None

    visited = set()
    for task_id in tasks:
        if task_id not in visited:
            result = dfs(task_id, [], visited, set())
            if result:
                return result

    return None


def generate_initial_state(parsed: dict) -> dict:
    """
    파싱된 태스크 정보로 초기 상태 파일 생성
    """
    from datetime import datetime

    pending = []
    completed = []

    for task_id, info in parsed["tasks"].items():
        if info["status"] == "completed":
            completed.append(task_id)
        else:
            pending.append(task_id)

    # 의존성 충족된 태스크를 ready로 이동
    ready = []
    remaining_pending = []

    for task_id in pending:
        deps = parsed["tasks"][task_id]["depends_on"]
        if all(d in completed for d in deps):
            ready.append(task_id)
        else:
            remaining_pending.append(task_id)

    return {
        "version": "2.0",
        "mode": "ultra-thin",
        "project": parsed["project"],
        "started_at": datetime.utcnow().isoformat() + "Z",
        "execution": {
            "current_phase": min(parsed["phases"]) if parsed["phases"] else 0,
            "parallel_limit": 5
        },
        "tasks": {
            "pending": remaining_pending,
            "ready": ready,
            "in_progress": [],
            "completed": completed,
            "failed": []
        },
        "task_details": {
            task_id: {
                "phase": info["phase"],
                "depends_on": info["depends_on"],
                "parallel_with": info["parallel_with"],
                "specialist": info["specialist"]
            }
            for task_id, info in parsed["tasks"].items()
        },
        "retry_counts": {},
        "error_log": [],
        "stats": {
            "total": parsed["total_tasks"],
            "completed": len(completed),
            "failed": 0,
            "success_rate": len(completed) / parsed["total_tasks"] if parsed["total_tasks"] > 0 else 0,
            "phases_completed": 0
        }
    }


def main():
    parser = argparse.ArgumentParser(description="TASKS.md 파서 - Ultra-Thin Orchestrate용")
    parser.add_argument("--input", "-i", required=True, help="TASKS.md 파일 경로")
    parser.add_argument("--output", "-o", help="출력 JSON 파일 경로")
    parser.add_argument("--state", "-s", action="store_true", help="초기 상태 파일도 생성")
    parser.add_argument("--state-output", help="상태 파일 출력 경로 (기본: .claude/orchestrate-state.json)")
    parser.add_argument("--check-circular", "-c", action="store_true", help="순환 의존성만 검사")

    args = parser.parse_args()

    # 파일 읽기
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR:TASKS_NOT_FOUND:{args.input}", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_text(encoding="utf-8")

    # 파싱
    parsed = parse_tasks_md(content)

    # 순환 의존성 검사
    circular = detect_circular_dependencies(parsed["tasks"])
    if circular:
        cycle_str = "->".join(circular)
        print(f"ERROR:CIRCULAR_DEP:{cycle_str}", file=sys.stderr)
        sys.exit(1)

    if args.check_circular:
        print("OK: 순환 의존성 없음")
        sys.exit(0)

    # 결과 출력
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"파싱 완료: {parsed['total_tasks']}개 태스크, {len(parsed['phases'])}개 Phase")
    else:
        print(json.dumps(parsed, indent=2, ensure_ascii=False))

    # 상태 파일 생성
    if args.state:
        state = generate_initial_state(parsed)
        state_path = Path(args.state_output or ".claude/orchestrate-state.json")
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"상태 파일 생성: {state_path}")


if __name__ == "__main__":
    main()
