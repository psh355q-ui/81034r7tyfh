#!/usr/bin/env python3
"""
문서 정리 자동화 스크립트 (Windows 호환)

- 30일 이상 된 일일 요약 → docs/archive/YYYY/MM/ 이동
- 중복 문서 감지 (같은 날짜 3개 이상)
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Windows Path Handling
BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "docs"
ARCHIVE_DIR = DOCS_DIR / "archive"
DAYS_TO_ARCHIVE = 30

def archive_old_daily_summaries():
    """30일 이상 된 일일 요약 아카이브"""
    if not DOCS_DIR.exists():
        print(f"Directory not found: {DOCS_DIR}")
        return

    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_ARCHIVE)
    print(f"Archiving files older than: {cutoff_date.date()}")

    count = 0
    for file in DOCS_DIR.glob("*.md"):
        # YYMMDD_*.md 형식 파싱 (6자리 이상, 처음 6자리가 숫자)
        if len(file.stem) >= 6 and file.stem[:6].isdigit():
            try:
                date_str = file.stem[:6]
                # 20년대 가정
                file_date = datetime.strptime(f"20{date_str}", "%Y%m%d")
                
                if file_date < cutoff_date:
                    # 아카이브 디렉토리 생성
                    year_month = file_date.strftime("%Y/%m")
                    archive_path = ARCHIVE_DIR / year_month
                    archive_path.mkdir(parents=True, exist_ok=True)

                    # 파일 이동
                    target_path = archive_path / file.name
                    if target_path.exists():
                        print(f"Skipping (Exists): {file.name}")
                    else:
                        shutil.move(str(file), str(target_path))
                        print(f"✅ Archived: {file.name} → {archive_path}")
                        count += 1
            except ValueError:
                continue
            except Exception as e:
                print(f"Error archiving {file.name}: {e}")

    print(f"Archived {count} files.")

def detect_duplicates():
    """같은 날짜 중복 문서 감지"""
    if not DOCS_DIR.exists():
        return

    date_files = {}
    for file in DOCS_DIR.glob("*.md"):
        if len(file.stem) >= 6 and file.stem[:6].isdigit():
            date = file.stem[:6]
            date_files.setdefault(date, []).append(file.name)

    print("\nChecking for duplicates...")
    found = False
    for date, files in date_files.items():
        if len(files) > 2:
            print(f"⚠️  Duplicates on {date} ({len(files)} files): {files}")
            found = True
    
    if not found:
        print("No excessive duplicates found.")

if __name__ == "__main__":
    archive_old_daily_summaries()
    detect_duplicates()
