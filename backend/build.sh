#!/bin/bash
# Railway 배포 전 빌드 스크립트

echo "Starting Railway build process..."

# Python 버전 확인
python --version

# 의존성 설치
pip install -r requirements.txt

# DB 초기화 (필요한 경우)
# python init_db.py

echo "Build complete!"
