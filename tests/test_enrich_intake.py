from lead_qualifier.enrich import enrich, facts_for
from lead_qualifier.intake import leads_from_csv, leads_from_text
from lead_qualifier.samples import sample_csv
from lead_qualifier.schema import Lead


def lead(i, email, t, msg="hello"):
    return Lead(id=i, email=email, message=msg, received_at=t)


def test_company_domain_and_country():
    f = facts_for(lead("a", "Hannah@KestrelFreight.co.uk", ""))
    assert f.domain == "kestrelfreight.co.uk" and f.website == "https://kestrelfreight.co.uk"
    assert f.country == "United Kingdom" and not f.free_email


def test_free_and_invalid_email():
    assert facts_for(lead("a", "x@gmail.com", "")).free_email
    assert facts_for(lead("a", "not-an-email", "")).invalid_email


def test_links_flagged():
    f = facts_for(lead("a", "", "", "see https://a.io and https://b.io"))
    assert f.links == 2 and f.flags


def test_duplicates_keep_the_earliest():
    leads = [lead("late", "g@lumen.it", "2026-11-24T10:00"), lead("early", "g@lumen.it", "2026-11-24T09:00"),
             lead("colleague", "m@lumen.it", "2026-11-24T11:00"), lead("other", "x@gmail.com", "2026-11-24T08:00"),
             lead("other2", "y@gmail.com", "2026-11-24T08:30")]  # fmt: skip
    f = enrich(leads)
    assert f["early"].duplicate_of is None
    assert f["late"].duplicate_of == "early"
    assert f["colleague"].duplicate_of == "early"  # same company domain
    assert f["other2"].duplicate_of is None  # gmail is not a company


def test_csv_with_unusual_headers():
    csv = (
        "First Name,Last Name,Work Email,Organisation,How can we help?,Created At\n"
        "Ana,Ruiz,ana@acme.es,Acme,Need a dashboard,2026-11-20 09:30\n,,,,,\n"
    )
    leads = leads_from_csv(csv.encode())
    assert len(leads) == 1
    assert (leads[0].name, leads[0].email, leads[0].company) == ("Ana Ruiz", "ana@acme.es", "Acme")
    assert leads[0].received_at.startswith("2026-11-20T09:30")


def test_csv_without_message_column_fails_clearly():
    try:
        leads_from_csv("name,email\na,b@c.de\n")
    except ValueError as exc:
        assert "message" in str(exc)
    else:
        raise AssertionError


def test_sample_csv_round_trips():
    assert len(leads_from_csv(sample_csv())) == 20


def test_pasted_text_splits_on_dashes():
    leads = leads_from_text("Hi, I'm ana@acme.es\nneed help\n---\nSecond lead here")
    assert [x.email for x in leads] == ["ana@acme.es", ""]
