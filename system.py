import json, argparse, sys, textwrap, random
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Literal, Dict
from pathlib import Path
from jinja2 import Template
from openai import OpenAI


'''
DB schema
ID PRIMARY_KEY INTEGER AUTO_INCREMENT,
PATH VARCHAR(255) NOT NULL,
VALUE VARCHAR(255) NOT NULL
UNIQUE(PATH, VALUE)
'''

# 전체 데이터 로드 : 피드백 입력값을 대치한 dict 저장
data = {}

# 임시 sample data 로드 : json형식으로 임시 작성
sample_data = {}

path_daily = set(["daily/lessonInfo/수업/수업_난이도/상", "daily/lessonInfo/수업/수업_난이도/중상", "daily/lessonInfo/수업/수업_난이도/중",  
    "daily/lessonInfo/수업/수업_난이도/중하", "daily/lessonInfo/수업/수업_난이도/하", "daily/studentInfos/studentInfo/숙제/지난_숙제_수행/수행_정도/90~100%", 
    "daily/studentInfos/studentInfo/숙제/지난_숙제_수행/수행_정도/70~90%", "daily/studentInfos/studentInfo/숙제/지난_숙제_수행/수행_정도/50~70%",
    "daily/studentInfos/studentInfo/숙제/지난_숙제_수행/수행_정도/50%이하", "daily/studentInfos/studentInfo/숙제/지난_숙제_수행/수행_정도/0%",
    "daily/studentInfos/studentInfo/숙제/특이사항/칭찬", "daily/studentInfos/studentInfo/숙제/특이사항/향상권고", "daily/studentInfos/studentInfo/숙제/특이사항/지난수업대비향상",
    "daily/studentInfos/studentInfo/숙제/특이사항/지난수업대비저하", "daily/studentInfos/studentInfo/숙제/특이사항/복습권장", "daily/studentInfos/studentInfo/테스트/성취도/상", 
    "daily/studentInfos/studentInfo/테스트/성취도/중상", "daily/studentInfos/studentInfo/테스트/성취도/중", "daily/studentInfos/studentInfo/테스트/성취도/중하",
    "daily/studentInfos/studentInfo/테스트/성취도/하", "daily/studentInfos/studentInfo/테스트/특이사항/칭찬", "daily/studentInfos/studentInfo/테스트/특이사항/성적향상",
    "daily/studentInfos/studentInfo/테스트/특이사항/성적하락", "daily/studentInfos/studentInfo/테스트/특이사항/복습권장", "daily/studentInfos/studentInfo/학생_피드백/출결/출석",
    "daily/studentInfos/studentInfo/학생_피드백/출결/지각", "daily/studentInfos/studentInfo/학생_피드백/출결/결석", "daily/studentInfos/studentInfo/학생_피드백/출결/조퇴",
    "daily/studentInfos/studentInfo/학생_피드백/출결/보강", "daily/studentInfos/studentInfo/학생_피드백/수업_이해도/상", "daily/studentInfos/studentInfo/학생_피드백/수업_이해도/중상",
    "daily/studentInfos/studentInfo/학생_피드백/수업_이해도/중", "daily/studentInfos/studentInfo/학생_피드백/수업_이해도/중하", "daily/studentInfos/studentInfo/학생_피드백/수업_이해도/하",
    "daily/studentInfos/studentInfo/학생_피드백/수업_참여도/적극적", "daily/studentInfos/studentInfo/학생_피드백/수업_참여도/일반적", "daily/studentInfos/studentInfo/학생_피드백/수업_참여도/소극적",
    "daily/studentInfos/studentInfo/학생_피드백/수업_태도/상", "daily/studentInfos/studentInfo/학생_피드백/수업_태도/중", "daily/studentInfos/studentInfo/학생_피드백/수업_태도/하",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/시_감상", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/소설_감상",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/극_수필_감상", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/독서_지문_분석",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/<보기>_연관_해석", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/선지_판단",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/어휘력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/문법_이해력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/시간_관리", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/개념원리_이해", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/계산_능력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/문제_해석", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/조건_분석", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/공식_활용",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/정답_도출", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/시간_활용", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/어휘력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/문법_이해력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/해석_능력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/듣기_능력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/말하기_능력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/쓰기_능력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/선지_판단",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/시간_활용",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/시_감상", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/소설_감상",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/극_수필_감상", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/독서_지문_분석",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/<보기>_연관_해석", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/선지_판단",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/어휘력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/문법_이해력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/시간_관리", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/개념원리_이해", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/계산_능력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/문제_해석", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/조건_분석", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/공식_활용",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/정답_도출", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/시간_활용", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/어휘력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/문법_이해력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/해석_능력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/듣기_능력",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/말하기_능력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/쓰기_능력", "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/선지_판단",
    "daily/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/시간_활용", "daily/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/전반적_양호", "daily/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/성실함",
    "daily/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/자기주도적_성격", "daily/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/성실함", "daily/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/컨디션_저하",
    "daily/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/동기부여_부족", "daily/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/지속적_성장", "daily/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/성장_정체기",
    "daily/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/자기주도적_학습", "daily/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/빠른_이해", "daily/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/노력_요함",
    "daily/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/격려_및_응원_요청", "daily/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/동기부여_요청", 
    "daily/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/가정_지도_요청"
    ])

path_weekly = set([
    "weekly/lessonInfo/수업/수업_난이도/상", "weekly/lessonInfo/수업/수업_난이도/중상", "weekly/lessonInfo/수업/수업_난이도/중", "weekly/lessonInfo/수업/수업_난이도/중하", "weekly/lessonInfo/수업/수업_난이도/하",
    "weekly/studentInfos/studentInfo/숙제/주간_숙제_수행_정도/90~100%", "weekly/studentInfos/studentInfo/숙제/주간_숙제_수행_정도/70~90%", "weekly/studentInfos/studentInfo/숙제/주간_숙제_수행_정도/50~70%", "weekly/studentInfos/studentInfo/숙제/주간_숙제_수행_정도/50%이하", "weekly/studentInfos/studentInfo/숙제/주간_숙제_수행_정도/0%",
    "weekly/studentInfos/studentInfo/숙제/특이사항/칭찬", "weekly/studentInfos/studentInfo/숙제/특이사항/향상권고", "weekly/studentInfos/studentInfo/숙제/특이사항/지난주대비향상", "weekly/studentInfos/studentInfo/숙제/특이사항/지난주대비저하", "weekly/studentInfos/studentInfo/숙제/특이사항/복습권장",
    "weekly/studentInfos/studentInfo/누적_테스트/성취도/상", "weekly/studentInfos/studentInfo/누적_테스트/성취도/중상", "weekly/studentInfos/studentInfo/누적_테스트/성취도/중", "weekly/studentInfos/studentInfo/누적_테스트/성취도/중하", "weekly/studentInfos/studentInfo/누적_테스트/성취도/하",
    "weekly/studentInfos/studentInfo/누적_테스트/특이사항/칭찬", "weekly/studentInfos/studentInfo/누적_테스트/특이사항/성적향상", "weekly/studentInfos/studentInfo/누적_테스트/특이사항/성적하락", "weekly/studentInfos/studentInfo/누적_테스트/특이사항/복습권장",
    "weekly/studentInfos/studentInfo/주간_테스트/성취도/상", "weekly/studentInfos/studentInfo/주간_테스트/성취도/중상", "weekly/studentInfos/studentInfo/주간_테스트/성취도/중", "weekly/studentInfos/studentInfo/주간_테스트/성취도/중하", "weekly/studentInfos/studentInfo/주간_테스트/성취도/하",
    "weekly/studentInfos/studentInfo/주간_테스트/특이사항/칭찬", "weekly/studentInfos/studentInfo/주간_테스트/특이사항/성적향상", "weekly/studentInfos/studentInfo/주간_테스트/특이사항/성적하락", "weekly/studentInfos/studentInfo/주간_테스트/특이사항/복습권장",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_이해도/상", "weekly/studentInfos/studentInfo/학생_피드백/수업_이해도/중상", "weekly/studentInfos/studentInfo/학생_피드백/수업_이해도/중", "weekly/studentInfos/studentInfo/학생_피드백/수업_이해도/중하", "weekly/studentInfos/studentInfo/학생_피드백/수업_이해도/하",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_참여도/적극적", "weekly/studentInfos/studentInfo/학생_피드백/수업_참여도/일반적", "weekly/studentInfos/studentInfo/학생_피드백/수업_참여도/소극적",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_태도/상", "weekly/studentInfos/studentInfo/학생_피드백/수업_태도/중", "weekly/studentInfos/studentInfo/학생_피드백/수업_태도/하",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/시_감상", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/소설_감상",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/극_수필_감상", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/독서_지문_분석",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/<보기>_연관_해석", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/선지_판단",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/어휘력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/문법_이해력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/시간_관리", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/개념원리_이해", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/계산_능력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/문제_해석", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/조건_분석", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/공식_활용",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/정답_도출", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/어휘력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/문법_이해력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/해석_능력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/듣기_능력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/말하기_능력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/쓰기_능력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/선지_판단", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/시간_활용",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/시_감상", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/소설_감상",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/극_수필_감상", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/독서_지문_분석",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/<보기>_연관_해석", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/선지_판단",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/어휘력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/문법_이해력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/시간_관리", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/개념원리_이해", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/계산_능력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/문제_해석", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/조건_분석", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/공식_활용",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/정답_도출", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/시간_활용", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/어휘력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/문법_이해력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/해석_능력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/듣기_능력",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/말하기_능력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/쓰기_능력", "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/선지_판단",
    "weekly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/시간_활용", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/전반적_양호", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/성실함",
    "weekly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/자기주도적_성격", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/성실함", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/컨디션_저하",
    "weekly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/동기부여_부족", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/지속적_성장", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/성장_정체기", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/빠른_이해", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/노력_요함",
    "weekly/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/격려_및_응원_요청", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/동기부여_요청", "weekly/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/가정_지도_요청"
])

path_monthly = set([
    "monthly/lessonInfo/수업/수업_난이도/상", "monthly/lessonInfo/수업/수업_난이도/중상", "monthly/lessonInfo/수업/수업_난이도/중", "monthly/lessonInfo/수업/수업_난이도/중하", "monthly/lessonInfo/수업/수업_난이도/하",
    "monthly/studentInfos/studentInfo/숙제/월간_숙제_수행_정도/90~100%", "monthly/studentInfos/studentInfo/숙제/월간_숙제_수행_정도/70~90%", "monthly/studentInfos/studentInfo/숙제/월간_숙제_수행_정도/50~70%", "monthly/studentInfos/studentInfo/숙제/월간_숙제_수행_정도/50%이하", "monthly/studentInfos/studentInfo/숙제/월간_숙제_수행_정도/0%",
    "monthly/studentInfos/studentInfo/숙제/특이사항/칭찬", "monthly/studentInfos/studentInfo/숙제/특이사항/향상권고", "monthly/studentInfos/studentInfo/숙제/특이사항/지난주대비향상", "monthly/studentInfos/studentInfo/숙제/특이사항/지난주대비저하", "monthly/studentInfos/studentInfo/숙제/특이사항/복습권장",
    "monthly/studentInfos/studentInfo/누적_테스트/성취도/상", "monthly/studentInfos/studentInfo/누적_테스트/성취도/중상", "monthly/studentInfos/studentInfo/누적_테스트/성취도/중", "monthly/studentInfos/studentInfo/누적_테스트/성취도/중하", "monthly/studentInfos/studentInfo/누적_테스트/성취도/하",
    "monthly/studentInfos/studentInfo/누적_테스트/특이사항/칭찬", "monthly/studentInfos/studentInfo/누적_테스트/특이사항/성적향상", "monthly/studentInfos/studentInfo/누적_테스트/특이사항/성적하락", "monthly/studentInfos/studentInfo/누적_테스트/특이사항/복습권장",
    "monthly/studentInfos/studentInfo/월간_테스트/성취도/상", "monthly/studentInfos/studentInfo/월간_테스트/성취도/중상", "monthly/studentInfos/studentInfo/월간_테스트/성취도/중", "monthly/studentInfos/studentInfo/월간_테스트/성취도/중하", "monthly/studentInfos/studentInfo/월간_테스트/성취도/하",
    "monthly/studentInfos/studentInfo/월간_테스트/특이사항/칭찬", "monthly/studentInfos/studentInfo/월간_테스트/특이사항/성적향상", "monthly/studentInfos/studentInfo/월간_테스트/특이사항/성적하락", "monthly/studentInfos/studentInfo/월간_테스트/특이사항/복습권장",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_이해도/상", "monthly/studentInfos/studentInfo/학생_피드백/수업_이해도/중상", "monthly/studentInfos/studentInfo/학생_피드백/수업_이해도/중", "monthly/studentInfos/studentInfo/학생_피드백/수업_이해도/중하", "monthly/studentInfos/studentInfo/학생_피드백/수업_이해도/하",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_참여도/적극적", "monthly/studentInfos/studentInfo/학생_피드백/수업_참여도/일반적", "monthly/studentInfos/studentInfo/학생_피드백/수업_참여도/소극적",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_태도/상", "monthly/studentInfos/studentInfo/학생_피드백/수업_태도/중", "monthly/studentInfos/studentInfo/학생_피드백/수업_태도/하",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/시_감상", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/소설_감상",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/극_수필_감상", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/독서_지문_분석",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/<보기>_연관_해석", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/선지_판단",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/어휘력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/문법_이해력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/국어/시간_관리", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/개념원리_이해", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/계산_능력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/문제_해석", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/조건_분석", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/공식_활용",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/수학/정답_도출", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/어휘력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/문법_이해력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/해석_능력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/듣기_능력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/말하기_능력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/쓰기_능력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/선지_판단", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_장/영어/시간_활용",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/시_감상", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/소설_감상",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/극_수필_감상", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/독서_지문_분석",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/<보기>_연관_해석", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/선지_판단",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/어휘력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/문법_이해력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/국어/시간_관리", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/개념원리_이해", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/계산_능력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/문제_해석", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/조건_분석", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/공식_활용",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/정답_도출", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/수학/시간_활용", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/어휘력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/문법_이해력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/해석_능력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/듣기_능력",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/말하기_능력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/쓰기_능력", "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/선지_판단",
    "monthly/studentInfos/studentInfo/학생_피드백/수업_성취도_단/영어/시간_활용", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/전반적_양호", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/성실함",
    "monthly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/자기주도적_성격", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/성실함", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/컨디션_저하",
    "monthly/studentInfos/studentInfo/학생_피드백/특이사항/학생_상태/동기부여_부족", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/지속적_성장", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/전반적_학습_상태/성장_정체기",
    "monthly/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/격려_및_응원_요청", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/동기부여_요청", "monthly/studentInfos/studentInfo/학생_피드백/특이사항/가정_지도사항/가정_지도_요청"
])


# --------------- 0. 함수 정의 --------------- #
def deep_merge(base: dict, override: dict) -> dict:
    """딕셔너리를 재귀적으로 병합하는 함수"""
    if not override:

        return base or {}

    if not base:

        return override

    out = dict(base)

    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):

            out[k] = deep_merge(out[k], v)

        else:

            out[k] = v

    return out


def set_replace_dict(origin_dict : dict, path : list, value : str):
    # dict 값 변경 함수 (피드백 중심 정보 대치)
    if isinstance(origin_dict, list):

        for i in origin_dict:
            set_replace_dict(i, path, value)
        return
    
    if isinstance(origin_dict, dict):

        key = path[0]

        if len(path) == 2:
            
            origin_dict[key] = value

        set_replace_dict(origin_dict[key], path[1:], value)


def rec_explore_dict(example_dict : dict, key : str, content: str, processed_keys: set = None):
    # 피드백 중심 정보 찾는 함수 (피드백 중심 정보 대치 함수 호출)
    global data

    if isinstance(example_dict[key], dict):

        for k, v in example_dict[key].items():
            rec_explore_dict(example_dict[key], k, content+"/"+k, processed_keys)

    elif isinstance(example_dict[key], list):

        for i in example_dict[key]:
            for j in list(i.keys()):
                rec_explore_dict(i, j, content+"/"+j, processed_keys)

    else:

        if type(example_dict[key]) != int and example_dict[key] != None:

            path = content + "/" + example_dict[key]

            if path in processed_keys: 

                global sample_data

                idx = random.randint(0, len(sample_data[path])-1)
                set_replace_dict(data, path.split("/")[1:], sample_data[path][idx])


def load_from_json_file(filename):

    try:

        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)            

    except Exception as e:

        print(f"{filename} 파일 내용을 읽어오는 중에 오류가 발생했습니다:\n{e}")


def ask_openai(system_prompt: str, user_prompt: str, model="ax4", temperature=0.6):
    
    client = OpenAI(base_url="https://guest-api.sktax.chat/v1",api_key="sktax-XyeKFrq67ZjS4EpsDlrHHXV8it")

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    return resp.choices[0].message.content.strip()


# --------------- 1. 맞춤 정보 --------------- #
class CustomInfo(BaseModel):
    피드백_형식: Literal["오늘 수업 피드백", "이번 주 피드백", "이번 달 피드백"] = Field(alias="피드백_형식")
    말투: Literal["문어체(~합니다)", "구어체(~해요)", "구어체(툭수문자 포함)"]
    양식: Literal["편지형", "정보형"]
    model_config = {"populate_by_name": True}


# --------------- 2. 수업 정보 --------------- #
class Lesson(BaseModel):
    수업_주차: Optional[str] = Field(None, alias="수업_주차")
    수업_단원: Optional[str] = Field(None, alias="수업_단원")
    수업_내용: Optional[str] = Field(None, alias="수업_내용")
    수업_난이도: Optional[str] = Field(None, alias="수업_난이도")
    진도_조정_여부: Optional[str] = Field(None, alias="진도_조정_여부")
    다음_주_예고: Optional[str] = Field(None, alias="다음_주_예고")
    다음_달_예고: Optional[str] = Field(None, alias="다음_달_예고")
    model_config = {"populate_by_name": True}

class Homework(BaseModel):
    진도_부분_문제풀이: Optional[str] = Field(None, alias="진도_부분_문제풀이")
    과제집_워크북: Optional[str] = Field(None, alias="과제집_워크북")
    오답_정리: Optional[str] = Field(None, alias="오답_정리")
    직접_입력: Optional[str] = Field(None, alias="직접_입력")
    model_config = {"populate_by_name": True}
    
class CumulativeTest(BaseModel):
    미니_테스트: Optional[int] = Field(None, alias="미니_테스트")
    단원_테스트: Optional[int] = Field(None, alias="단원_테스트")
    정규_테스트: Optional[int] = Field(None, alias="정규_테스트")
    직접_입력: Optional[str] = Field(None, alias="직접_입력")
    model_config = {"populate_by_name": True}

class Test(BaseModel):
    테스트_내용: Optional[str] = Field(None, alias="테스트_내용")
    만점: Optional[int] = None
    통과_기준: Optional[int] = None
    반_평균: Optional[int] = None
    반_최고점: Optional[int] = None
    반_최저점: Optional[int] = None
    model_config = {"populate_by_name": True}

class LessonInfo(BaseModel):
    수업: Optional[Lesson] = None
    숙제: Optional[Homework] = None
    누적_테스트: Optional[CumulativeTest] = None
    테스트: Optional[Dict[str, Test]] = None
    model_config = {"populate_by_name": True}


# --------------- 3. 학생 정보 --------------- #
class HomeworkTask(BaseModel):
    숙제명: Optional[str] = Field(None, alias="숙제명")
    수행_정도: Optional[str] = Field(None, alias="수행_정도")
    model_config = {"populate_by_name": True}

class PersonalCumulativeTest(BaseModel):
    성취도: Optional[str] = None
    특이사항: Optional[List[str]] = Field(None, alias="특이사항")
    model_config = {"populate_by_name": True}

class PersonalTest(BaseModel):
    테스트_내용: Optional[str] = Field(None, alias="테스트_내용")
    획득_점수: Optional[str] = Field(None, alias="획득_점수")
    성취도: Optional[str] = None
    통과_여부: Optional[str] = Field(None, alias="통과_여부")
    석차: Optional[int] = None
    특이사항: Optional[List[str]] = Field(None, alias="특이사항")
    model_config = {"populate_by_name": True}

class PersonalHomework(BaseModel):
    지난_숙제_수행: Optional[List[HomeworkTask]] = Field(None, alias="지난_숙제_수행")
    주간_숙제_수행_정도: Optional[str] = Field(None, alias="주간_숙제_수행_정도")
    월간_숙제_수행_정도: Optional[str] = Field(None, alias="월간_숙제_수행_정도")
    특이사항: Optional[List[str]] = Field(None, alias="특이사항")
    model_config = {"populate_by_name": True}

class SubjectAchievement(BaseModel):
    수학: Optional[str] = None
    국어: Optional[str] = None
    영어: Optional[str] = None
    model_config = {"populate_by_name": True}

class PersonalFeedbackDetail(BaseModel):
    학생_상태: Optional[List[str]] = Field(None, alias="학생_상태")
    전반적_학습_상태: Optional[List[str]] = Field(None, alias="전반적_학습_상태")
    가정_지도사항: Optional[List[str]] = Field(None, alias="가정_지도사항")
    model_config = {"populate_by_name": True}

class PersonalFeedback(BaseModel):
    출결: Optional[str] = Field(None, alias="출결")
    정상_출석_일수: Optional[int] = Field(None, alias="정상_출석_일수")
    이상_출석_일수: Optional[int] = Field(None, alias="이상_출석_일수")
    이상_출석_사유: Optional[str] = Field(None, alias="이상_출석_사유")
    수업_이해도: Optional[str] = Field(None, alias="수업_이해도")
    수업_참여도: Optional[str] = Field(None, alias="수업_참여도")
    수업_태도: Optional[str] = Field(None, alias="수업_태도")
    수업_성취도_장: Optional[SubjectAchievement] = Field(None, alias="수업_성취도_장")
    수업_성취도_단: Optional[SubjectAchievement] = Field(None, alias="수업_성취도_단")
    특이사항: Optional[PersonalFeedbackDetail] = Field(None, alias="특이사항")
    model_config = {"populate_by_name": True}

class StudentInfo(BaseModel):
    학생_이름: Optional[str] = Field(None, alias="학생_이름")
    숙제: Optional[PersonalHomework] = None
    누적_테스트: Optional[PersonalCumulativeTest] = None
    테스트: Optional[Dict[str, PersonalTest]] = None
    학생_피드백: Optional[PersonalFeedback] = None
    model_config = {"populate_by_name": True}

class StudentInfos(BaseModel):
    userGroupId: Optional[int] = None
    studentInfo: Optional[StudentInfo] = None
    model_config = {"populate_by_name": True}

class InputPayload(BaseModel):
    customInfo: Optional[CustomInfo] = None
    lessonInfo: Optional[LessonInfo] = None
    studentInfos: Optional[List[StudentInfos]] = None
    model_config = {"populate_by_name": True}


SYSTEM_PROMPT = Template(textwrap.dedent("""
당신은 학원 강사로서 중·고등학생에 대한 {{format}}을 학부모님께 전달합니다.
입력되는 정보를 바탕으로 피드백 메세지를 작성합니다.

규칙:
0. 첫 문장은 학부모님께 보내는 가벼운 인삿말로 시작
 - 예: 오늘도 [학생이름] 학생과 함께 수업 잘 마쳤습니다.
 - 예: 안녕하세요~ 오늘 [학생이름] 수업에 대한 피드백 문자 전송드려요.
1. 작성자는 선생님이며, 학생을 제3자로 지칭하지 않습니다.
2. 학생의 성(lastname)은 생략하고, 이름(first name)만 사용합니다.
 - 예: 김주원 → 주원이는, 주원이가, 주원 학생은, 주원이와,... / 권진아 → 진아는, 진아가, 진아 학생이, 진아와, ...
3. 중·고등학생의 눈높이에 맞게 내용 구성하며, 학부모님께 예의 바르고 부드러운 존댓말로 작성
4. 강점과 개선점을 균형 있게 다루되, 상충되거나 반복되는 표현은 피합니다.
5. 분량은 400자 ~ 600자 사이로 작성합니다.
6. 내용별 2~3개의 짧은 문단으로 구분
7. 학부모님께 전하는 가벼운 인삿말로 마무리 합니다. 이때, 학부모님께 함께 노력하기를 당부하는 표현은 삼가해주세요.
"""))

LETTER_PROMPT_TMPL = Template(textwrap.dedent("""

아래 입력된 정보를 바탕으로 중·고등학생 자녀를 둔 학부모님께 발송할 수업 피드백 메세지를 {{tone}}로 작성해주세요.

{% if lesson -%}
[수업]
{% if lesson.get("수업_주차") -%}
    - 주차 : {{ lesson.수업_주차 }}
{% endif -%}
{% if lesson.get("수업_단원") -%}
    - 단원 : {{ lesson.수업_단원 }}
{% endif -%}
{% if lesson.get("수업_내용") -%}
    - 내용 : {{ lesson.수업_내용 }}
{% endif -%}
{% if lesson.get("수업_난이도") -%}
    - {{ lesson.수업_난이도 }}
{% endif -%}
{% if lesson.get("진도_조정_여부") -%}
    - 진도 조정 여부 : {{ lesson.진도_조정_여부 }}
{% endif -%}
{% if lesson.get("다음_주_예고") -%}
    - 다음 주 예고 : {{ lesson.다음_주_예고 }}
{% endif -%}
{% if lesson.get("다음_달_예고") -%}
    - 다음 달 예고 : {{ lesson.다음_달_예고 }}
{% endif -%}
{% endif %}
{% if homework.get("지난_숙제_수행") -%}
[지난 숙제 피드백]
{% for h in homework.get("지난_숙제_수행") -%}
    {% if h.get("숙제명") -%}
    - 숙제명 : {{h.get("숙제명")}}
    {% endif -%}
    {% if h.get("수행_정도") -%}
    - 수행 정도 : {{h.get("수행_정도")}}
    {% endif -%}
{% endfor -%}
{% if homework.get("주간_숙제_수행_정도") -%}
    - 주간 숙제 수행 정도 : {{ homework.주간_숙제_수행_정도 }}
{% endif -%}
{% if homework.get("월간_숙제_수행_정도") -%}
    - 월간 숙제 수행 정도 : {{ homework.월간_숙제_수행_정도 }}
{% endif -%}
{% if homework.get("특이사항") -%}
{% for t in homework.get("특이사항") -%}
    - {{t[1]}}
{% endfor -%}
{% endif -%}
{% endif %}
{% if homework.get("진도_부분_문제풀이") or homework.get("과제집_워크북") or homework.get("오답_정리") or homework.get("직접_입력") -%}
[이번 주 숙제 안내]
{% if homework.get("진도_부분_문제풀이") -%}
    - 진도 부분 문제풀이 : {{ homework.진도_부분_문제풀이 }}
{% endif -%}
{% if homework.get("과제집_워크북") -%}
    - 과제집 워크북 : {{ homework.과제집_워크북 }}
{% endif -%}
{% if homework.get("오답_정리") -%}
    - 오답 정리 : {{ homework.오답_정리 }}
{% endif -%}
{% if homework.get("직접_입력") -%}
    - 직접 입력 : {{ homework.직접_입력 }}
{% endif -%}
{% endif %}
{% if test -%}
[테스트 결과 피드백]
{% for t in test.keys() -%}
{% if test.get(t).get("테스트_내용") -%}
    - 테스트 내용 : {{test.get(t).테스트_내용}}
{% endif -%}
{% if test.get(t).get("만점") -%}
    - 만점 : {{test.get(t).만점}}
{% endif -%}
{% if test.get(t).get("통과_기준") -%}
    - 통과 기준 : {{test.get(t).통과_기준}}
{% endif -%}
{% if test.get(t).get("반_평균") -%}
    - 반 평균 : {{test.get(t).반_평균}}
{% endif -%}
{% if test.get(t).get("반_최고점") -%}
    - 반 최고점 : {{test.get(t).반_최고점}}
{% endif -%}
{% if test.get(t).get("반_최저점") -%}
    - 반 최저점 : {{test.get(t).반_최저점}}
{% endif -%}
{% if test.get(t).get("획득_점수") -%}
    - 획득 점수 : {{test.get(t).획득_점수}}
{% endif -%}
{% if test.get(t).get("성취도") -%}
    - 성취도 : {{test.get(t).성취도}}
{% endif -%}
{% if test.get(t).get("통과_여부") -%}
    - 통과 여부 : {{test.get(t).통과_여부}}
{% endif -%}
{% if test.get(t).get("석차") -%}
    - 석차 : {{test.get(t).석차}}
{% endif -%}
{% if test.get(t).get("특이사항") -%}
    - 특이사항 : {{test.get(t).특이사항 | join(", ")}}
{% endif -%}
{% endfor -%}
{% endif %} 
{% if cumulative_test -%}
[누적 테스트]
{% if cumulative_test.get("미니_테스트") -%}
    - 미니 테스트 : {{cumulative_test.미니_테스트}}
{% endif -%}
{% if cumulative_test.get("단원_테스트") -%}
    - 단원 테스트 : {{cumulative_test.단원_테스트}}
{% endif -%}
{% if cumulative_test.get("정규_테스트") -%}
    - 단원 테스트 : {{cumulative_test.정규_테스트}}
{% endif -%}
{% if cumulative_test.get("직접_입력") -%}
    - 단원 테스트 : {{cumulative_test.직접_입력}}
{% endif -%}
{% if cumulative_test.get("성취도") -%}
    - {{cumulative_test.get("성취도")}}
{% endif -%}
{% if cumulative_test.get("특이사항") -%}
    {% for i in cumulative_test.get("특이사항") -%}
    - {{i}}
    {% endfor -%}
{% endif -%}
{% endif %}
{% if stu_fd -%}
[학생 피드백]
{% if stu_fd.get("출결") -%}
    - 출결 : {{stu_fd.get("출결")}}
{% endif -%}
{% if stu_fd.get("정상_출석_일수") -%}
    - 정상 출석 일수 : {{stu_fd.정상_출석_일수}}
{% endif -%}
{% if stu_fd.get("이상_출석_일수") -%}
    - 이상 출석 일수 : {{stu_fd.이상_출석_일수}}
{% endif -%}
{% if stu_fd.get("이상_출석_사유") -%}
    - 이상 출석 사유 : {{stu_fd.이상_출석_사유}}
{% endif -%}
{% if stu_fd.get("수업_이해도") -%}
    - 수업 이해도 : {{stu_fd.수업_이해도}}
{% endif -%}
{% if stu_fd.get("수업_참여도") -%}
    - 수업 참여도 : {{stu_fd.수업_참여도}}
{% endif -%}
{% if stu_fd.get("수업_태도") -%}
    - 수업 태도 : {{stu_fd.수업_태도}}
{% endif -%}
{% if stu_fd.get("수업_성취도_장") -%}
    - 수업 성취도 장
{% if stu_fd.수업_성취도_장.get("수학") -%}
        - 수학 : {{stu_fd.수업_성취도_장.수학}}
{% endif -%}
{% if stu_fd.수업_성취도_장.get("국어") -%}
        - 국어 : {{stu_fd.수업_성취도_장.국어}}
{% endif -%}
{% if stu_fd.수업_성취도_장.get("영어") -%}
        - 영어 : {{stu_fd.수업_성취도_장.영어}}
{% endif -%}
{% endif -%}
{% if stu_fd.get("수업_성취도_단") -%}
    - 수업 성취도 단
{% if stu_fd.수업_성취도_단.get("수학") -%}
        - 수학 : {{stu_fd.수업_성취도_단.수학}}
{% endif -%}
{% if stu_fd.수업_성취도_단.get("국어") -%}
        - 국어 : {{stu_fd.수업_성취도_단.국어}}
{% endif -%}
{% if stu_fd.수업_성취도_단.get("영어") -%}
        - 영어 : {{stu_fd.수업_성취도_단.영어}}
{% endif -%}
{% endif -%}
{% if stu_fd.get("특이사항") -%}
    - 특이사항
{% if stu_fd.get("특이사항").get("학생상태") -%}
        - 학생상태 : {{stu_fd.특이사항.학생상태| join(", ")}}
{% endif -%}
{% if stu_fd.get("특이사항").get("전반적_학습_상태") -%}
        - 전반적 학습 상태 : {{stu_fd.특이사항.전반적_학습_상태 | join(", ")}}
{% endif -%}
{% if stu_fd.get("특이사항").get("가정_지도사항") -%}
        - 가정 지도사항 : {{stu_fd.특이사항.가정_지도사항 | join(", ")}}
{% endif -%}
{% if stu_fd.get("특이사항").get("직접입력") -%}
        - 직접 입력 : {{stu_fd.특이사항.직접입력}}
{% endif -%}
{% endif -%}
{% endif %}

요구사항
0) {{name}} 학생 이름을 자연스럽게 추가합니다. 이때, 학생의 성(lastname)은 생략하고, 이름(first name)만 사용합니다. 예: 오늘도 주원이는, 주원이가, 주원 학생은, 주원이와,... / 안녕하세요~ 오늘 진아는, 진아가, 진아 학생이, 진아와, ...
1) 입력된 피드백을 종합하여 하나의 피드백 메세지로 구성. 이때 최대한 위 내용을 참고하여 빠지는 내용없이 작성(중속되거나 상충되는 내용은 생략하며, 큰 내용의 틀을 벗어나지 않도롭 합니다.)
2) 숙제는 범주구분을 명확히 해주세요. 지난 숙제에 대한 피드백과 이번숙제에 대한 정보가 모두 있는 경우 두 범주로 나누어 작성합니다.
"""))

INFO_PROMPT_TMPL = Template(textwrap.dedent("""
아래 입력된 정보를 바탕으로 중·고등학생 자녀를 둔 학부모님께 발송할 수업 피드백 메세지를 {{tone}}로 작성해주세요.

{% if lesson -%}
[수업]
{% if lesson.get("수업_난이도") -%}
    - {{ lesson.수업_난이도 }}
{% endif -%}
{% endif %}
{% if cumulative_test -%}
[누적 테스트]
{% if cumulative_test.get("성취도") -%}
    - {{cumulative_test.get("성취도")}}
{% endif -%}
{% if cumulative_test.get("특이사항") -%}
    {% for i in cumulative_test.get("특이사항") -%}
    - {{i}}
    {% endfor -%}
{% endif -%}
{% endif -%}
{% if stu_fd -%}
[학생 피드백]
{% if stu_fd.get("출결") -%}
    - 출결 : {{stu_fd.get("출결")}}
{% endif -%}
{% if stu_fd.get("수업_이해도") -%}
    - {{stu_fd.get("수업_이해도")}}
{% endif -%}
{% if stu_fd.get("수업_참여도") -%}
    - {{stu_fd.get("수업_참여도")}}
{% endif -%}
{% if stu_fd.get("수업_태도") -%}
    - 수업 태도 : {{stu_fd.get("수업_태도")}}
{% endif -%}
{% if stu_fd.get("수업_성취도_장") -%}
    - 수업 성취도 장
    {% if stu_fd.get("수업_성취도_장").get("수학") -%}
        - 수학 : {{stu_fd.get("수업_성취도_장").get("수학")}}
    {% endif -%}
    {% if stu_fd.get("수업_성취도_장").get("국어") -%}
        - 국어 : {{stu_fd.get("수업_성취도_장").get("국어")}}
    {% endif -%}
    {% if stu_fd.get("수업_성취도_장").get("영어") -%}
        - 영어 : {{stu_fd.get("수업_성취도_장").get("영어")}}
    {% endif -%}
{% endif -%}
{% if stu_fd.get("수업_성취도_단") -%}
    - 수업 성취도 단
    {% if stu_fd.get("수업_성취도_단").get("수학") -%}
        - 수학 : {{stu_fd.get("수업_성취도_단").get("수학")}}
    {% endif -%}
    {% if stu_fd.get("수업_성취도_단").get("국어") -%}
        - 국어 : {{stu_fd.get("수업_성취도_단").get("국어")}}
    {% endif -%}
    {% if stu_fd.get("수업_성취도_단").get("영어") -%}
        - 영어 : {{stu_fd.get("수업_성취도_단").get("영어")}}
    {% endif -%}
{% endif -%}
{% if stu_fd.get("특이사항") -%}
    - 특이사항
    {% if stu_fd.get("특이사항").get("학생상태") -%}
        - 학생상태 : {{stu_fd.get("특이사항").get("학생상태")}}
    {% endif -%}
    {% if stu_fd.get("특이사항").get("전반적_학습_상태") -%}
        - 전반적 학습 상태 : {{stu_fd.get("특이사항").get("전반적_학습_상태")}}
    {% endif -%}
    {% if stu_fd.get("특이사항").get("가정_지도사항") -%}
        - 가정 지도사항 : {{stu_fd.get("특이사항").get("가정_지도사항")}}
    {% endif -%}
{% endif -%}
{% endif %}


요구사항
0) {{name}} 학생 이름을 자연스럽게 추가합니다. 이때, 학생의 성(lastname)은 생략하고, 이름(first name)만 사용합니다. 예: 오늘도 주원이는, 주원이가, 주원 학생은, 주원이와,... / 안녕하세요~ 오늘 진아는, 진아가, 진아 학생이, 진아와, ...
1) 입력된 피드백을 종합하여 하나의 피드백 메세지로 구성. 이때 최대한 위 내용을 참고하여 빠지는 내용없이 작성(중속되거나 상충되는 내용은 생략하며, 큰 내용의 틀을 벗어나지 않도롭 합니다.)
2) 숙제는 범주구분을 명확히 해주세요. 지난 숙제에 대한 피드백과 이번숙제에 대한 정보가 모두 있는 경우 두 범주로 나누어 작성합니다.
3) 인사는 생략해줘.
"""))


INFO_TMPL = Template(textwrap.dedent("""
안녕하세요. {{name}} 학생의 {{format}} 입니다.

{% set idx = 0 -%}
{% if attendance.get("정상_출석_일수") or attendance.get("이상_출석_일수") or attendance.get("이상_출석_사유") -%}
{% set idx = idx + 1 -%}
{{idx}}. 출결 현황
{% if attendance.get("정상_출석_일수") -%}
    - 정상 출석 일수 : {{attendance.정상_출석_일수}}
{% endif -%}
{% if attendance.get("이상_출석_일수") -%}
    - 이상 출석 일수 : {{attendance.이상_출석_일수}}
{% endif -%}
{% if attendance.get("이상_출석_사유") -%}
    - 이상 출석 사유 : {{attendance.이상_출석_사유}}
{% endif -%}
{% endif %}
{% if lesson -%}
{% set idx = idx + 1 -%}
{{idx}}. 수업 내용
{% if lesson.get("수업_주차") -%}
    - 주차 : {{ lesson.수업_주차 }}
{% endif -%}
{% if lesson.get("수업_단원") -%}
    - 단원 : {{ lesson.수업_단원 }}
{% endif -%}
{% if lesson.get("수업_내용") -%}
    - 내용 : {{ lesson.수업_내용 }}
{% endif -%}
{% if lesson.get("진도_조정_여부") -%}
    - 진도 조정 여부 : {{ lesson.진도_조정_여부 }}
{% endif -%}
{% if lesson.get("다음_주_예고") -%}
    - 다음 주 예고 : {{ lesson.다음_주_예고 }}
{% endif -%}
{% if lesson.get("다음_달_예고") -%}
    - 다음 달 예고 : {{ lesson.다음_달_예고 }}
{% endif -%}
{% endif %}
{% if homework.get("지난_숙제_수행") -%}
{% set idx = idx + 1 -%}
{{idx}}. 지난 숙제 안내
{% for h in homework.get("지난_숙제_수행") -%}
    {% if h.get("숙제명") and h.get("수행_정도") -%}
    - {{h.get("숙제명")}} : {{h.get("수행_정도")}}
    {% endif -%}
{% endfor -%}
{% if homework.get("주간_숙제_수행_정도") -%}
    - 주간 숙제 수행 정도 : {{ homework.주간_숙제_수행_정도 }}
{% endif -%}
{% if homework.get("월간_숙제_수행_정도") -%}
    - 월간 숙제 수행 정도 : {{ homework.월간_숙제_수행_정도 }}
{% endif -%}
{% endif %}
{% if homework.get("진도_부분_문제풀이") or homework.get("과제집_워크북") or homework.get("오답_정리") or homework.get("직접_입력") -%}
{% set idx = idx + 1 -%}
{{idx}}. 이번 주 숙제 안내
{% if homework.get("진도_부분_문제풀이") -%}
    - 진도 부분 문제풀이 : {{ homework.진도_부분_문제풀이 }}
{% endif -%}
{% if homework.get("과제집_워크북") -%}
    - 과제집 워크북 : {{ homework.과제집_워크북 }}
{% endif -%}
{% if homework.get("오답_정리") -%}
    - 오답 정리 : {{ homework.오답_정리 }}
{% endif -%}
{% if homework.get("직접_입력") -%}
    - {{ homework.직접_입력 }}
{% endif -%}
{% endif %}
{% if test -%}
{% set idx = idx + 1 -%}
{{idx}}. 테스트
{% for t in test.keys() -%}
{% if test.get(t).get("테스트_내용") -%}
    - 테스트 내용 : {{test.get(t).테스트_내용}}
{% endif -%}
{% if test.get(t).get("만점") -%}
    - 만점 : {{test.get(t).만점}}
{% endif -%}
{% if test.get(t).get("통과_기준") -%}
    - 통과 기준 : {{test.get(t).통과_기준}}
{% endif -%}
{% if test.get(t).get("반_평균") -%}
    - 반 평균 : {{test.get(t).반_평균}}
{% endif -%}
{% if test.get(t).get("반_최고점") -%}
    - 반 최고점 : {{test.get(t).반_최고점}}
{% endif -%}
{% if test.get(t).get("반_최저점") -%}
    - 반 최저점 : {{test.get(t).반_최저점}}
{% endif -%}
{% if test.get(t).get("획득_점수") -%}
    - 획득 점수 : {{test.get(t).획득_점수}}
{% endif -%}
{% if test.get(t).get("통과_여부") -%}
    - 통과 여부 : {{test.get(t).통과_여부}}
{% endif -%}
{% if test.get(t).get("석차") -%}
    - 석차 : {{test.get(t).석차}}
{% endif -%}
{% endfor -%}
{% endif %}
{% if cumulative_test -%}
{% set idx = idx + 1 -%}
{{idx}}. 누적 테스트
{% if cumulative_test.get("미니_테스트") -%}
    - 미니 테스트 : {{cumulative_test.미니_테스트}}
{% endif -%}
{% if cumulative_test.get("단원_테스트") -%}
    - 단원 테스트 : {{cumulative_test.단원_테스트}}
{% endif -%}
{% if cumulative_test.get("정규_테스트") -%}
    - 단원 테스트 : {{cumulative_test.정규_테스트}}
{% endif -%}
{% if cumulative_test.get("직접_입력") -%}
    - 단원 테스트 : {{cumulative_test.직접_입력}}
{% endif -%}
{% endif %}
{% if stu_fd -%}
{% set idx = idx + 1 -%}
{{idx}}. 학생 피드백
{{stu_fd}}
{% endif %}

이상으로 {{name}} 학생의 {{format}}을 마치겠습니다.
감사합니다.
"""))

def main():

    global data
    global sample_data

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", type=Path, help="입력 JSON 파일 경로")
    ap.add_argument("-o", "--output", type=Path, help="출력 JSON 파일 경로")
    ap.add_argument("--model", default="ax4", help="사용할 OpenAI 모델")
    ap.add_argument("--debug", action="store_true", help="디버그 모드")
    args = ap.parse_args()
    
    data = json.loads(args.input.read_text("utf-8") if args.input else sys.stdin.read())
    sample_data = load_from_json_file("/Users/chaejimin/Desktop/서울대학교/2-2/하계 방학/클래스 데이/feedback/sample/sample.json")
    system_prompt = ""

    customInfo = data["customInfo"]
    keys = list(data.keys())[1:]
    
    # Daily, Weekly, Monthly 에 따라 대치
    if customInfo["피드백_형식"] == "오늘 수업 피드백":
        system_prompt = SYSTEM_PROMPT.render(type = "오늘 수업 피드백")
        for key in keys:
            rec_explore_dict(data, key, "daily/" + key, path_daily)

    elif customInfo["피드백_형식"] == "이번 주 피드백":
        system_prompt = SYSTEM_PROMPT.render(type = "주간 피드백")
        for key in keys:
            rec_explore_dict(data, key, "weekly/" + key, path_weekly)

    elif customInfo["피드백_형식"] == "이번 달 피드백":
        system_prompt = SYSTEM_PROMPT.render(type = "월간 피드백")
        for key in keys:
            rec_explore_dict(data, key, "monthly/" + key, path_monthly)

    else:
        raise ValueError("Invalid plan")

    payload = InputPayload.model_validate(data)
    lesson_info = payload.lessonInfo.model_dump(exclude_none=True) if payload.lessonInfo else {}
    student_infos = payload.studentInfos
    
    # 편지형, 정보형 피드백 처리
    if customInfo["양식"] == "편지형":

        for stu in student_infos:
            student_data = stu.model_dump(exclude_none=True)["studentInfo"]
            merged = deep_merge(lesson_info, student_data)

            user_prompt = LETTER_PROMPT_TMPL.render(
                tone = customInfo["말투"],
                name = merged.get("학생_이름"),
                lesson = merged.get("수업"),
                homework = merged.get("숙제"),
                test = merged.get("테스트"),
                cumulative_test = merged.get("누적_테스트"),
                stu_fd = merged.get("학생_피드백")
            )  

            feedback = ask_openai(system_prompt, user_prompt, args.model, 0.6)

            print(feedback)


    elif customInfo["양식"] == "정보형":

        for stu in student_infos:
            student_data = stu.model_dump(exclude_none=True)["studentInfo"]
            merged = deep_merge(lesson_info, student_data)   
            
            # 피드백 중심 입력값으로 피드백 생성
            user_prompt = INFO_PROMPT_TMPL.render(
                tone = customInfo["말투"],
                name = merged.get("학생_이름"),
                homework = merged.get("숙제"),
                test = merged.get("테스트"),
                cumulative_test = merged.get("누적_테스트"),
                stu_fd = merged.get("학생_피드백")
            )

            feedback = ask_openai(system_prompt, user_prompt, args.model, 0.6)

            #정보 중심 입력값 + 피드백 중심 입력값 통합 템플릿 처리   cf) 학생_피드백에 출결 정보 존재
            message = INFO_TMPL.render(
                format = customInfo["피드백_형식"],
                tone = customInfo["말투"],
                name = merged.get("학생_이름"),
                lesson = merged.get("수업"),
                homework = merged.get("숙제"),
                test = merged.get("테스트"),
                cumulative_test = merged.get("누적_테스트"),
                attendance = merged.get("학생_피드백"),         
                stu_fd = feedback
            )

            print(message)

    else:
        raise ValueError("Invalid format")

if __name__ == "__main__":
    main()
