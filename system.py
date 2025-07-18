import json, sys, argparse, os, textwrap
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from typing import Literal, Optional, List, Dict, Union

from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI, OpenAIError
from jinja2 import Template, StrictUndefined


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
    미니_테스트: Optional[str] = Field(None, alias="미니_테스트")
    단원_테스트: Optional[str] = Field(None, alias="단원_테스트")
    정규_테스트: Optional[str] = Field(None, alias="정규_테스트")
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
    테스트: Optional[List[Test]] = None
    model_config = {"populate_by_name": True}


# --------------- 3. 학생 정보 --------------- #
class HomeworkTask(BaseModel):
    숙제명: Optional[str] = Field(None, alias="숙제명")
    수행_정도: Optional[str] = Field(None, alias="수행_정도")
    model_config = {"populate_by_name": True}

class PersonalCumulativeTest(BaseModel):
    성취도: Optional[str] = None
    특이_사항: Optional[List[str]] = Field(None, alias="특이_사항")
    model_config = {"populate_by_name": True}

class PersonalTest(BaseModel):
    테스트_내용: Optional[str] = Field(None, alias="테스트_내용")
    획득_점수: Optional[str] = Field(None, alias="획득_점수")
    성취도: Optional[str] = None
    통과_여부: Optional[str] = Field(None, alias="통과_여부")
    석차: Optional[int] = None
    특이_사항: Optional[List[str]] = Field(None, alias="특이_사항")
    model_config = {"populate_by_name": True}

class PersonalHomework(BaseModel):
    지난_숙제_수행: Optional[List[HomeworkTask]] = Field(None, alias="지난_숙제_수행")
    주간_숙제_수행_정도: Optional[str] = Field(None, alias="주간_숙제_수행_정도")
    월간_숙제_수행_정도: Optional[str] = Field(None, alias="월간_숙제_수행_정도")
    특이_사항: Optional[List[str]] = Field(None, alias="특이_사항")
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
    출결: Optional[str] = None
    정상_출석_일수: Optional[int] = Field(None, alias="정상_출석_일수")
    이상_출석_일수: Optional[int] = Field(None, alias="이상_출석_일수")
    이상_출석_사유: Optional[str] = Field(None, alias="이상_출석_사유")
    수업_이해도: Optional[str] = Field(None, alias="수업_이해도")
    수업_참여도: Optional[str] = Field(None, alias="수업_참여도")
    수업_태도: Optional[str] = Field(None, alias="수업_태도")
    수업_성취도_장: Optional[SubjectAchievement] = Field(None, alias="수업_성취도_장")
    수업_성취도_단: Optional[SubjectAchievement] = Field(None, alias="수업_성취도_단")
    특이_사항: Optional[PersonalFeedbackDetail] = Field(None, alias="특이_사항")
    model_config = {"populate_by_name": True}

class StudentInfo(BaseModel):
    학생_이름: Optional[str] = Field(None, alias="학생_이름")
    숙제: Optional[PersonalHomework] = None
    누적_테스트: Optional[PersonalCumulativeTest] = None
    테스트: Optional[List[PersonalTest]] = None
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


# --------------- 4. 시스템 프롬프트 --------------- #
SYSTEM_PROMPT = """
당신은 학원 강사로서 중·고등학생에 대한 피드백을 학부모님께 전달합니다.
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
6. 내용별 2~3개의 짧은 문단으로 구분
7. 학부모님께 전하는 가벼운 인삿말로 마무리 합니다. 이때, 학부모님께 함께 노력하기를 당부하는 표현은 삼가해주세요.
"""

DAILY_PROMPT_TMPL = Template(textwrap.dedent("""
아래 입력된 정보를 바탕으로 중·고등학생 자녀를 둔 학부모님께 발송할 수업 피드백 메세지를 {{tone}}로 작성해주세요.

{% if lesson.수업 %}
[수업]
{% if lesson.수업.수업_주차 %}
- 주차 : {{ lesson.수업.수업_주차 }}
{% endif %}
{% if lesson.수업.수업_단원 %}
- 단원 : {{ lesson.수업.수업_단원 }}
{% endif %}
{% if lesson.수업.수업_내용 %}
- 내용 : {{ lesson.수업.수업_내용 }}
{% endif %}
{% if lesson.수업.수업_난이도 %}
- 난이도 : {{ lesson.수업.수업_난이도 }}
{% endif %}
{% endif %}

{% if homework %}
[이번 주 숙제 안내]
{% if homework.진도_부분_문제풀이 %}
- 진도 부분 문제풀이 : {{ homework.진도_부분_문제풀이 }}
{% endif %}
{% if homework.과제집_워크북 %}
- 과제집 워크북 : {{ homework.과제집_워크북 }}
{% endif %}
{% if homework.오답_정리 %}
- 오답 정리 : {{ homework.오답_정리 }}
{% endif %}
{% if homework.직접_입력 %}
- 직접 입력 : {{ homework.직접_입력 }}
{% endif %}
{% endif %}



요구사항
0) {{student}} 학생 이름을 자연스럽게 추가합니다. 이때, 학생의 성(lastname)은 생략하고, 이름(first name)만 사용합니다. 예: 오늘도 주원이는, 주원이가, 주원 학생은, 주원이와,... / 안녕하세요~ 오늘 진아는, 진아가, 진아 학생이, 진아와, ...
1) 입력된 피드백을 종합하여 하나의 피드백 메세지로 구성. 이때 최대한 위 내용을 참고하여 빠지는 내용없이 작성(중속되거나 상충되는 내용은 생략하며, 큰 내용의 틀을 벗어나지 않도롭 합니다.)
2) 숙제는 범주구분을 명확히 해주세요. 지난 숙제에 대한 피드백과 이번숙제에 대한 정보가 모두 있는 경우 두 범주로 나누어 작성합니다.
"""))

WEEKLY_PROMPT_TMPL = Template(textwrap.dedent("""
"""))

MONTHLY_PROMPT_TMPL = Template(textwrap.dedent("""
"""))

INFORMATION_DAILY_PROMPT_TMPL = Template(textwrap.dedent("""
"""))

INFORMATION_WEEKLY_PROMPT_TMPL = Template(textwrap.dedent("""
"""))

INFORMATION_MONTHLY_PROMPT_TMPL = Template(textwrap.dedent("""
"""))

INFORMATION_DAILY_TMPL = Template(textwrap.dedent("""
"""))

INFORMATION_WEEKLY_TMPL = Template(textwrap.dedent("""
"""))

INFORMATION_MONTHLY_TMPL = Template(textwrap.dedent("""
"""))


def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", type=Path, help="입력 JSON 파일 경로")
    ap.add_argument("-o", "--output", type=Path, help="출력 JSON 파일 경로")
    ap.add_argument("--model", default="gpt-4o-mini", help="사용할 OpenAI 모델")
    ap.add_argument("--debug", action="store_true", help="디버그 모드")
    args = ap.parse_args()

    raw = (args.input.read_text("utf-8") if args.input else sys.stdin.read())

    try:
        data = InputPayload.model_validate_json(raw)
    except ValidationError as ve:
        print(f"입력 검증 실패:\n{ve}")
        sys.exit(1)

    custom_info = data.customInfo
    lesson_info = data.lessonInfo.model_dump(exclude_none=True) if data.lessonInfo else {}
    student_infos = data.studentInfos
    
    for stu in student_infos:
        if custom_info.양식 == "편지형":
            if custom_info.피드백_형식 == "오늘 수업 피드백":

                student_data = stu.model_dump(exclude_none=True)
                merged = deep_merge(lesson_info, student_data)

                print(merged)

                user_prompt = DAILY_PROMPT_TMPL.render(
                    tone = custom_info.말투,
                    student=stu.studentInfo.학생_이름,
                    lesson=merged.get("수업"),
                    homework=merged.get("숙제"),
                    test=merged.get("테스트"),
                    stu_fb=merged.get("학생_피드백")
                )

                print(user_prompt)

            elif custom_info.피드백_형식 == "이번 주 피드백":

                student_data = stu.model_dump(exclude_none=True)
                merged = deep_merge(lesson_info, student_data)

                user_prompt = WEEKLY_PROMPT_TMPL.render(
                    tone = custom_info.말투,
                    student=stu.학생_이름,
                    lesson=merged.get("수업"),
                    homework=merged.get("숙제"),
                    test=merged.get("테스트"),
                    cumulative_test=merged.get("누적_테스트"),
                    stu_fb=merged.get("학생_피드백")
                )
            else:
                student_data = stu.model_dump(exclude_none=True)
                merged = deep_merge(lesson_info, student_data)

                user_prompt = MONTHLY_PROMPT_TMPL.render(
                    tone = custom_info.말투,
                    student=stu.학생_이름,
                    lesson=merged.get("수업"),
                    homework=merged.get("숙제"),
                    test=merged.get("테스트"),
                    cumulative_test=merged.get("누적_테스트"),
                    stu_fb=merged.get("학생_피드백")
                )
        else: # 정보형 피드백 처리
            if custom_info.피드백_형식 == "오늘 수업 피드백":

                student_data = stu.model_dump(exclude_none=True)
                merged = deep_merge(lesson_info, student_data)

                user_prompt = INFORMATION_DAILY_PROMPT_TMPL.render(
                    tone = custom_info.말투,
                    student=stu.studentInfo.학생_이름,
                    lesson=merged.get("수업"),
                    homework=merged.get("숙제"),
                    test=merged.get("테스트"),
                    stu_fb=merged.get("학생_피드백")
                )

            elif custom_info.피드백_형식 == "이번 주 피드백":

                student_data = stu.model_dump(exclude_none=True)
                merged = deep_merge(lesson_info, student_data)

                user_prompt = WEEKLY_PROMPT_TMPL.render(
                    tone = custom_info.말투,
                    student=stu.학생_이름,
                    lesson=merged.get("수업"),
                    homework=merged.get("숙제"),
                    test=merged.get("테스트"),
                    cumulative_test=merged.get("누적_테스트"),
                    stu_fb=merged.get("학생_피드백")
                )
            else:
                student_data = stu.model_dump(exclude_none=True)
                merged = deep_merge(lesson_info, student_data)

                user_prompt = MONTHLY_PROMPT_TMPL.render(
                    tone = custom_info.말투,
                    student=stu.학생_이름,
                    lesson=merged.get("수업"),
                    homework=merged.get("숙제"),
                    test=merged.get("테스트"),
                    cumulative_test=merged.get("누적_테스트"),
                    stu_fb=merged.get("학생_피드백")
                )

    
    
if __name__ == "__main__":
    main()
    