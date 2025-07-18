import json

def prune_nulls(obj):
    """
    재귀적으로 obj를 순회하면서,
    - dict인 경우: value가 None이 아닌 항목만 남기고, 재귀 호출하여 내부도 정리
    - list인 경우: 각 요소에 재귀 호출
    - 그 외: 그대로 반환
    """
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if v is None or v == "" :
                continue
            pruned_v = prune_nulls(v)
            cleaned[k] = pruned_v
        return cleaned
    elif isinstance(obj, list):
        return [prune_nulls(item) for item in obj]
    else:
        return obj

# 사용 예시
if __name__ == "__main__":
    # JSON 문자열을 로드
    with open("./input_structure.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # null 값 제거
    cleaned_data = prune_nulls(data)

    # 결과 확인
    print(json.dumps(cleaned_data, ensure_ascii=False, indent=2))
