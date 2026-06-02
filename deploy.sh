#!/bin/bash

# Jarvis Telegram Bot Deployment Helper Script

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Jarvis Telegram Bot Deployment Helper ===${NC}\n"

# 1. Check if git is configured
echo -e "${BLUE}[1/3] Git holatini tekshirish...${NC}"
if [ -d .git ]; then
    echo -e "${GREEN}✓ Git muvaffaqiyatli initsializatsiya qilingan.${NC}"
else
    git init
    git add .
    git commit -m "Initial commit"
    echo -e "${GREEN}✓ Git yangidan yaratildi va fayllar kiritildi.${NC}"
fi

# 2. Add GitHub remote repository
echo -e "\n${BLUE}[2/3] GitHub Repozitoriy Bog'lash...${NC}"
echo -e "Iltimos, GitHub'dagi yangi shaxsiy repozitoriyingiz URL manzilini kiriting:"
echo -e "(Masalan: https://github.com/username/jarvis-telegram-bot.git)"
read -p "GitHub Repo URL: " REPO_URL

if [ -n "$REPO_URL" ]; then
    git remote remove origin 2>/dev/null
    git remote add origin "$REPO_URL"
    git branch -M main
    
    echo -e "\nGitHub'ga yuklanmoqda..."
    if git push -u origin main; then
        echo -e "${GREEN}✓ Kodlar GitHub'ga muvaffaqiyatli yuklandi!${NC}"
    else
        echo -e "${RED}✗ GitHub'ga yuklashda xatolik yuz berdi. Iltimos, havola va ruxsatlaringizni tekshiring.${NC}"
    fi
else
    echo -e "Bog'lanish bekor qilindi. Keyinchalik o'zingiz yuklashingiz mumkin."
fi

# 3. Google OAuth Token extract for Railway
echo -e "\n${BLUE}[3/3] Railway uchun Google OAuth Token tayyorlash...${NC}"
if [ -f token.json ]; then
    echo -e "${GREEN}✓ token.json fayli topildi!${NC}"
    echo -e "Quyidagi matnni nusxalab oling va Railway'dagi ${GREEN}GOOGLE_TOKEN_JSON${NC} muhit o'zgaruvchisiga (Variable) qo'ying:\n"
    echo -e "${BLUE}------------------------------------------------------------${NC}"
    cat token.json
    echo -e "\n${BLUE}------------------------------------------------------------${NC}"
else
    echo -e "${RED}✗ token.json fayli topilmadi.${NC}"
    echo -e "Railway'ga deploy qilishdan oldin, iltimos, botni o'z kompyuteringizda bir marta ishga tushiring:"
    echo -e "  1. credentials.json faylini loyiha papkasiga joylang."
    echo -e "  2. python3 bot.py ni ishlating va brauzer orqali ruxsat bering."
    echo -e "  3. Keyin ushbu skriptni qayta ishga tushirsangiz, sizga Railway uchun kalitni tayyorlab beradi."
fi

echo -e "\n${GREEN}Tayyor! Rahmat.${NC}"
