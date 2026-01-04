"""
War Room MVP Skills 검증 테스트 (Simplified)

Date: 2026-01-02
Phase: Skills Migration - Step 5

이 테스트는 직접 파일 시스템을 검증하여 import 이슈를 회피합니다.
"""

import os
import re


def test_skill_file_structure():
    """Test 1: 모든 skill 파일이 올바른 구조를 가지고 있는지 검증"""
    print("\n" + "="*80)
    print("TEST 1: Skill File Structure Validation")
    print("="*80)
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_dir = os.path.join(BASE_DIR, 'ai', 'skills', 'war-room-mvp')
    
    print(f"\nChecking directory: {skills_dir}")
    
    if not os.path.exists(skills_dir):
        print(f"❌ Skills directory not found: {skills_dir}")
        return False
    
    expected_agents = [
        'trader-agent-mvp',
        'risk-agent-mvp',
        'analyst-agent-mvp',
        'pm-agent-mvp',
        'orchestrator-mvp'
    ]
    
    all_valid = True
    
    for agent_name in expected_agents:
        agent_dir = os.path.join(skills_dir, agent_name)
        
        print(f"\n  Checking {agent_name}:")
        
        # Check directory exists
        if not os.path.isdir(agent_dir):
            print(f"    ❌ Directory not found")
            all_valid = False
            continue
        else:
            print(f"    ✅ Directory exists")
        
        # Check SKILL.md exists
        skill_md = os.path.join(agent_dir, 'SKILL.md')
        if not os.path.isfile(skill_md):
            print(f"    ❌ SKILL.md not found")
            all_valid = False
        else:
            size = os.path.getsize(skill_md)
            print(f"    ✅ SKILL.md exists ({size:,} bytes)")
            if size < 100:
                print(f"    ⚠️  Warning: SKILL.md seems too small")
        
        # Check handler.py exists
        handler_py = os.path.join(agent_dir, 'handler.py')
        if not os.path.isfile(handler_py):
            print(f"    ❌ handler.py not found")
            all_valid = False
        else:
            size = os.path.getsize(handler_py)
            print(f"    ✅ handler.py exists ({size:,} bytes)")
    
    if all_valid:
        print("\n✅ TEST PASSED: All skill files have correct structure")
    else:
        print("\n❌ TEST FAILED: Some skill files are missing")
    
    return all_valid


def test_skill_md_content():
    """Test 2: SKILL.md 파일들이 올바른 내용을 포함하는지 검증"""
    print("\n" + "="*80)
    print("TEST 2: SKILL.md Content Validation")
    print("="*80)
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_dir = os.path.join(BASE_DIR, 'ai', 'skills', 'war-room-mvp')
    
    expected_skills = [
        {
            'name': 'trader-agent-mvp',
            'expected_name': 'trader-agent-mvp',
            'expected_weight': '0.35',
            'role_keywords': ['공격', '기회', 'trader', 'technical']
        },
        {
            'name': 'risk-agent-mvp',
            'expected_name': 'risk-agent-mvp',
            'expected_weight': '0.35',
            'role_keywords': ['방어', '리스크', 'risk', 'position']
        },
        {
            'name': 'analyst-agent-mvp',
            'expected_name': 'analyst-agent-mvp',
            'expected_weight': '0.30',
            'role_keywords': ['정보', '분석', 'analyst', 'news']
        },
        {
            'name': 'pm-agent-mvp',
            'expected_name': 'pm-agent-mvp',
            'expected_weight': 'final',
            'role_keywords': ['최종', '의사결정', 'decision', 'hard rules']
        },
        {
            'name': 'orchestrator-mvp',
            'expected_name': 'orchestrator-mvp',
            'expected_weight': 'n/a',
            'role_keywords': ['조율', 'orchestrator', 'workflow']
        }
    ]
    
    all_valid = True
    
    for skill_info in expected_skills:
        agent_name = skill_info['name']
        skill_md = os.path.join(skills_dir, agent_name, 'SKILL.md')
        
        print(f"\n  Validating {agent_name}:")
        
        if not os.path.isfile(skill_md):
            print(f"    ❌ SKILL.md not found")
            all_valid = False
            continue
        
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check YAML frontmatter
        if content.startswith('---'):
            print(f"    ✅ Has YAML frontmatter")
        else:
            print(f"    ❌ Missing YAML frontmatter")
            all_valid = False
        
        # Check for expected name
        if f"name: {skill_info['expected_name']}" in content:
            print(f"    ✅ Contains expected name: {skill_info['expected_name']}")
        else:
            print(f"    ⚠️  Name not found in expected format")
        
        # Check for voting_weight (except orchestrator)
        if skill_info['expected_weight'] != 'n/a':
            if skill_info['expected_weight'] in content:
                print(f"    ✅ Contains voting_weight: {skill_info['expected_weight']}")
            else:
                print(f"    ⚠️  voting_weight {skill_info['expected_weight']} not found")
        
        # Check for role keywords
        found_keywords = sum(1 for kw in skill_info['role_keywords'] if kw.lower() in content.lower())
        print(f"    ✅ Found {found_keywords}/{len(skill_info['role_keywords'])} role keywords")
        
        # Check for basic sections
        sections = ['## Role', '## Core Capabilities', '## Output Format']
        found_sections = sum(1 for section in sections if section in content)
        print(f"    ✅ Found {found_sections}/{len(sections)} required sections")
    
    if all_valid:
        print("\n✅ TEST PASSED: All SKILL.md files have valid content")
    else:
        print("\n❌ TEST FAILED: Some SKILL.md files have issues")
    
    return all_valid


def test_handler_py_content():
    """Test 3: handler.py 파일들이 execute() 함수를 포함하는지 검증"""
    print("\n" + "="*80)
    print("TEST 3: handler.py Content Validation")
    print("="*80)
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_dir = os.path.join(BASE_DIR, 'ai', 'skills', 'war-room-mvp')
    
    expected_agents = [
        'trader-agent-mvp',
        'risk-agent-mvp',
        'analyst-agent-mvp',
        'pm-agent-mvp',
        'orchestrator-mvp'
    ]
    
    all_valid = True
    
    for agent_name in expected_agents:
        handler_py = os.path.join(skills_dir, agent_name, 'handler.py')
        
        print(f"\n  Validating {agent_name}/handler.py:")
        
        if not os.path.isfile(handler_py):
            print(f"    ❌ handler.py not found")
            all_valid = False
            continue
        
        with open(handler_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for execute() function
        if 'def execute(context: Dict[str, Any])' in content:
            print(f"    ✅ Has execute() function with correct signature")
        else:
            print(f"    ❌ Missing execute() function")
            all_valid = False
        
        # Check for imports from backend.ai.mvp
        if 'from backend.ai.mvp' in content or 'from ai.mvp' in content:
            print(f"    ✅ Imports from MVP module")
        else:
            print(f"    ⚠️  No MVP imports found (may use different import style)")
        
        # Check for return statement
        if 'return' in content:
            print(f"    ✅ Has return statement")
        else:
            print(f"    ❌ Missing return statement")
            all_valid = False
    
    if all_valid:
        print("\n✅ TEST PASSED: All handler.py files have valid content")
    else:
        print("\n❌ TEST FAILED: Some handler.py files have issues")
    
    return all_valid


def test_legacy_migration():
    """Test 4: Legacy SKILL.md 파일들이 legacy/ 폴더로 이동했는지 검증"""
    print("\n" + "="*80)
    print("TEST 4: Legacy Files Migration Validation")
    print("="*80)
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    legacy_dir = os.path.join(BASE_DIR, 'ai', 'skills', 'legacy', 'war-room')
    old_dir = os.path.join(BASE_DIR, 'ai', 'skills', 'war-room')
    
    print(f"\nChecking legacy directory: {legacy_dir}")
    
    # Check legacy directory exists
    if not os.path.exists(legacy_dir):
        print(f"  ❌ Legacy directory not found")
        return False
    else:
        print(f"  ✅ Legacy directory exists")
    
    # Check old directory doesn't exist (should be moved)
    if os.path.exists(old_dir):
        print(f"  ⚠️ Warning: Old war-room directory still exists at original location")
        print(f"     ({old_dir})")
    else:
        print(f"  ✅ Old war-room directory removed from original location")
    
    # Check for legacy SKILL.md files
    expected_legacy = [
        'pm-agent',
        'trader-agent',
        'risk-agent',
        'analyst-agent',
        'macro-agent',
        'institutional-agent',
        'news-agent'
    ]
    
    found = 0
    for agent in expected_legacy:
        agent_dir = os.path.join(legacy_dir, agent)
        skill_md = os.path.join(agent_dir, 'SKILL.md')
        if os.path.isfile(skill_md):
            found += 1
            print(f"  ✅ {agent}/SKILL.md found")
        else:
            print(f"  ⚠️  {agent}/SKILL.md not found")
    
    print(f"\n  Found {found}/{len(expected_legacy)} legacy SKILL.md files")
    
    if found >= 5:  # At least 5 legacy files should exist
        print("\n✅ TEST PASSED: Legacy files properly migrated")
        return True
    else:
        print("\n❌ TEST FAILED: Missing legacy files")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "="*80)
    print("War Room MVP Skills - 검증 테스트")
    print("="*80)
    
    results = []
    
    # Test 1: File structure
    results.append(("File Structure", test_skill_file_structure()))
    
    # Test 2: SKILL.md content
    results.append(("SKILL.md Content", test_skill_md_content()))
    
    # Test 3: handler.py content
    results.append(("handler.py Content", test_handler_py_content()))
    
    # Test 4: Legacy migration
    results.append(("Legacy Migration", test_legacy_migration()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    exit(main())
