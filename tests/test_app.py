from streamlit.testing.v1 import AppTest


def test_dashboard_renders_samples():
    at = AppTest.from_file("../app.py", default_timeout=60).run()
    assert not at.exception
    assert at.title[0].value.endswith("Lead Qualifier")
    assert at.metric[0].value == "20"


def test_paste_a_lead_offline():
    at = AppTest.from_file("../app.py", default_timeout=60).run()
    at.sidebar.radio[0].set_value("Paste text").run()
    at.sidebar.text_area[0].input("Hi, I own a bakery and want a website. Budget €3k, next month. jo@bakery.it").run()
    next(b for b in at.sidebar.button if b.label == "Qualify leads").click().run()
    assert not at.exception
    assert at.metric[0].value == "21"
