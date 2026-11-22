from pathlib import Path

import pytest

from load_scores import load_scores


# 이 테스트 파일이 저장된 폴더
BASE_DIR = Path(__file__).resolve().parent


def make_csv(tmp_path, filename, data):
    """기존 scores.csv의 헤더를 사용해 임시 CSV를 만든다."""
    source = BASE_DIR / "scores.csv"

    with source.open(encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\r\n")

    path = tmp_path / filename
    path.write_text(header + "\n" + data, encoding="utf-8")
    return str(path)


# 정상 ①: 기존 정상 파일에서 5개를 읽는지 확인
def test_정상_파일을_읽는다():
    path = BASE_DIR / "scores.csv"

    kept, skipped = load_scores(str(path))

    assert len(kept) == 5


# 정상 ②: 빈 줄은 기록 없이 건너뛰는지 확인
def test_빈_줄은_건너뛴다(tmp_path):
    path = make_csv(
        tmp_path,
        "blank_lines.csv",
        "홍길동,80\n\n김영희,90\n",
    )

    kept, skipped = load_scores(path)

    assert kept == [("홍길동", 80), ("김영희", 90)]
    assert skipped == []


# 정상 ③: 따옴표 안의 쉼표를 이름의 일부로 읽는지 확인
def test_이름에_쉼표가_있어도_읽는다(tmp_path):
    path = make_csv(
        tmp_path,
        "comma_name.csv",
        '"홍,길동",80\n',
    )

    kept, skipped = load_scores(path)

    assert kept == [("홍,길동", 80)]
    assert skipped == []


# 예외 ①: 없는 파일이면 FileNotFoundError가 발생하는지 확인
def test_없는_파일이면_오류가_난다(tmp_path):
    path = tmp_path / "not_exist.csv"

    with pytest.raises(FileNotFoundError):
        load_scores(str(path))


# 예외 ②: 헤더만 있으면 빈 결과 두 개를 반환하는지 확인
def test_헤더만_있으면_빈_결과(tmp_path):
    path = make_csv(tmp_path, "header_only.csv", "")

    kept, skipped = load_scores(path)

    assert kept == []
    assert skipped == []


# 경계값: -1, 0, 1, 99, 100, 101점을 각각 검사
@pytest.mark.parametrize(
    "score, expected_kept, expected_skipped_count",
    [
        (-1, [], 1),
        (0, [("홍길동", 0)], 0),
        (1, [("홍길동", 1)], 0),
        (99, [("홍길동", 99)], 0),
        (100, [("홍길동", 100)], 0),
        (101, [], 1),
    ],
    ids=[
        "score_minus_1",
        "score_0",
        "score_1",
        "score_99",
        "score_100",
        "score_101",
    ],
)
def test_점수_경계값(
    tmp_path,
    score,
    expected_kept,
    expected_skipped_count,
):
    path = make_csv(
        tmp_path,
        "boundary.csv",
        f"홍길동,{score}\n",
    )

    kept, skipped = load_scores(path)

    assert kept == expected_kept
    assert len(skipped) == expected_skipped_count

    # 범위 밖인 -1점과 101점은 건너뛴 기록도 확인
    if expected_skipped_count == 1:
        line_number, original_line, reason = skipped[0]

        assert line_number == 2
        assert original_line.strip() == f"홍길동,{score}"
        assert isinstance(reason, str)
        assert reason.strip() != ""

def test_이름이_비어_있으면_건너뛴다(tmp_path):
    path = make_csv(
        tmp_path,
        "empty_name.csv",
        ",80\n",
    )

    kept, skipped = load_scores(path)

    assert kept == []
    assert len(skipped) == 1

    line_number, original_line, reason = skipped[0]

    assert line_number == 2
    assert original_line.strip() == ",80"
    assert reason == "이름이 비어 있음"       

    