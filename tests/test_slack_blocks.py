from panda.slack.blocks import choice_message, error_message, preview_message, status_message


def test_status_message():
    blocks = status_message("Scanning...")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "section"


def test_choice_message():
    options = [{"id": "0", "label": "Data 1"}, {"id": "1", "label": "Data 2"}]
    blocks = choice_message("Pick one:", options)
    assert len(blocks) == 2
    assert blocks[1]["type"] == "actions"
    # 2 options + "All" button = 3 buttons
    assert len(blocks[1]["elements"]) == 3


def test_preview_message():
    blocks = preview_message("test.csv", "col1  col2\n1     2", 100, 5, "/data/test.csv")
    assert len(blocks) == 2
    assert "100" in blocks[0]["text"]["text"]


def test_error_message():
    blocks = error_message("Something broke")
    assert ":x:" in blocks[0]["text"]["text"]
