#!/usr/bin/env python3
"""
Automatic Logging Decorator Applier

Scans a router file and applies @log_endpoint decorator to all endpoints.
"""

import re
import sys
from pathlib import Path


def extract_router_info(content: str) -> tuple:
    """Extract router prefix and agent info"""
    # Find router prefix
    prefix_match = re.search(r'router\s*=\s*APIRouter\([^)]*prefix=["\']([^"\']+)', content)
    prefix = prefix_match.group(1) if prefix_match else "/api/unknown"
    
    # Guess agent name from prefix
    agent_name = prefix.split('/')[-1].replace('-', '_')
    
    # Guess category
    category = "system"  # default
    if "news" in agent_name or "analysis" in agent_name:
        category = "analysis"
    elif "trade" in agent_name or "signal" in agent_name:
        category = "trading"
    elif "war" in agent_name or "debate" in agent_name:
        category = "war-room"
    
    return agent_name, category


def find_endpoints(content: str) -> list:
    """Find all endpoint function definitions"""
    # Pattern: @router.METHOD("/path")
    pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'][^)]*\)\s*\n(?:@\w+[^\n]*\n)*\s*(?:async\s+)?def\s+(\w+)'
    
    matches = re.finditer(pattern, content, re.MULTILINE)
    endpoints = []
    
    for match in matches:
        method = match.group(1).upper()
        path = match.group(2)
        func_name = match.group(3)
        line_num = content[:match.start()].count('\n') + 1
        
        endpoints.append({
            'method': method,
            'path': path,
            'func_name': func_name,
            'line_num': line_num,
            'decorator_line': match.group(0).split('\n')[0]  # @router line
        })
    
    return endpoints


def apply_decorator(file_path: Path, agent_name: str, category: str):
    """Apply logging decorator to all endpoints in the file"""
    
    content = file_path.read_text(encoding='utf-8')
    
    # Check if already has decorator import
    if 'from backend.ai.skills.common.logging_decorator import log_endpoint' in content:
        print(f"⚠️  {file_path.name} already has decorator import, skipping")
        return False
    
    # Find endpoints
    endpoints = find_endpoints(content)
    
    if not endpoints:
        print(f"⚠️  No endpoints found in {file_path.name}")
        return False
    
    print(f"\n📝 {file_path.name}: Found {len(endpoints)} endpoints")
    for ep in endpoints:
        print(f"   - {ep['method']} {ep['path']} ({ep['func_name']})")
    
    # Add import
    import_line = "from backend.ai.skills.common.logging_decorator import log_endpoint\n"
    
    # Find where to insert import (after other imports)
    import_section_end = 0
    for i, line in enumerate(content.split('\n')):
        if line.startswith('from ') or line.startswith('import '):
            import_section_end = i + 1
    
    lines = content.split('\n')
    lines.insert(import_section_end, import_line.rstrip())
    content = '\n'.join(lines)
    
    # Add decorator to each endpoint
    for ep in reversed(endpoints):  # Reverse to preserve line numbers
        decorator = f"@log_endpoint(\"{agent_name}\", \"{category}\")\n"
        
        # Find the @router line
        pattern = re.escape(ep['decorator_line']) + r'\s*\n'
        replacement = ep['decorator_line'] + '\n' + decorator
        
        content = re.sub(pattern, replacement, content, count=1)
    
    # Write back
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Applied decorator to {len(endpoints)} endpoints in {file_path.name}")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_logging.py <router_file.py>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    content = file_path.read_text(encoding='utf-8')
    agent_name, category = extract_router_info(content)
    
    print(f"🔍 Router: {file_path.name}")
    print(f"   Agent: {agent_name}")
    print(f"   Category: {category}")
    
    success = apply_decorator(file_path, agent_name, category)
    
    if success:
        print(f"\n✅ Done! Remember to test: python -c \"from backend.api.{file_path.stem} import router\"")
    else:
        print(f"\n⚠️  Skipped {file_path.name}")


if __name__ == "__main__":
    main()
