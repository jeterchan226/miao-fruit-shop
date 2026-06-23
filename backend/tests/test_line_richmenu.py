from app.services import line_service


def test_build_rich_menu_request_layout():
    req = line_service.build_rich_menu_request("1234567890-AbcdEfgh")

    assert req.size.width == 2500
    assert req.size.height == 843
    assert req.chat_bar_text == "選單"
    assert len(req.areas) == 3

    area_a, area_c, area_f = req.areas

    assert area_a.bounds.x == 0
    assert area_a.bounds.width == 833
    assert area_a.action.uri == "https://liff.line.me/1234567890-AbcdEfgh"

    assert area_c.bounds.x == 833
    assert area_c.bounds.width == 833
    assert area_c.action.data == "action=report_payment"
    assert area_c.action.display_text == "我要回報匯款"

    assert area_f.bounds.x == 1666
    assert area_f.bounds.width == 834
    assert area_f.action.data == "action=purchase_notice"
    assert area_f.action.display_text == "購買須知"
