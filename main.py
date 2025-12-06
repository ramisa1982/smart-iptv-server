name: Update Channels Daily

on:
  schedule:
    - cron: '0 0 * * *'  # يعمل كل يوم منتصف الليل
  workflow_dispatch:      # زر التشغيل اليدوي

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # إذن الكتابة ضروري

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # مهم جداً لتجنب مشاكل التاريخ

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10' # تم التحديث لحل المشكلة الصفراء

      - name: Install libraries
        run: pip install -r requirements.txt

      - name: Run AI Script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python main.py

      # --- هذا هو الحل السحري للمشكلة الحمراء ---
      - name: Pull latest changes
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git pull origin main --rebase || git pull origin main

      - name: Commit and Push changes
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "Updated Channel List via AI"
          file_pattern: "playlist_active.m3u"
