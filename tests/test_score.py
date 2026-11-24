from lead_qualifier.enrich import enrich
from lead_qualifier.samples import PROFILE, sample_leads
from lead_qualifier.schema import Lead, LeadRead
from lead_qualifier.score import Rules, score_all, score_lead


def read(**kw) -> LeadRead:
    base = dict(
        lead_type="prospect", summary="x", matched_service="AI automation", budget_signal="stated_fits",
        budget_amount=9000, budget_currency="EUR", timeline="now", authority="decision_maker",
        company_size="small", intent="high", next_action="book_call",
    )  # fmt: skip
    return LeadRead(**{**base, **kw})


def scored(r: LeadRead, email="ana@acme-logistics.it", rules=None):
    lead = Lead(id="A", email=email, message="hi", received_at="2026-11-24T10:00+00:00")
    return score_lead(lead, r, enrich([lead])["A"], PROFILE, rules or Rules())


def test_perfect_lead_scores_100_and_is_hot():
    s = scored(read())
    assert s.score == 100 and s.tier == "Hot"
    assert sum(p for _, p in s.reasons) == 100


def test_every_point_has_a_reason():
    s = scored(read(timeline="later", authority="influencer"))
    assert s.score == sum(p for _, p in s.reasons)
    assert any("Influencer" in why for why, _ in s.reasons)


def test_budget_below_minimum_is_capped_at_nurture():
    s = scored(read(budget_signal="stated_below", budget_amount=800))
    assert s.tier == "Nurture"


def test_non_buyers_are_disqualified_with_zero_score():
    for t in ("spam", "vendor_pitch", "job_seeker", "student_or_research"):
        s = scored(read(lead_type=t))
        assert (s.tier, s.score, s.deal_value) == ("Disqualified", 0, 0)


def test_existing_customers_are_routed_not_sold_to():
    assert scored(read(lead_type="existing_customer")).tier == "Route"


def test_disposable_email_is_disqualified():
    assert scored(read(), email="x@mailinator.com").tier == "Disqualified"


def test_free_email_penalty_only_for_company_leads():
    company = scored(read(company_size="mid"), email="boss@gmail.com")
    solo = scored(read(company_size="solo"), email="coach@gmail.com")
    assert any("free email" in w for w, _ in company.reasons)
    assert not any("free email" in w for w, _ in solo.reasons)


def test_rules_change_the_tier():
    r = read(timeline="this_quarter", intent="medium", company_size="unknown")
    assert scored(r).tier == "Hot"  # 20+25+12+15+3+5 = 80
    assert scored(r, rules=Rules(hot_at=85)).tier == "Warm"


def test_deal_value_converts_currency_and_falls_back_to_service_price():
    assert scored(read(budget_amount=10000, budget_currency="GBP")).deal_value == 11700
    assert scored(read(budget_signal="none", budget_amount=None)).deal_value == 8000


def test_reply_deadline_follows_tier():
    s = scored(read())
    assert s.reply_by.isoformat() == "2026-11-24T11:00:00+00:00"


def test_sample_queue_has_every_tier_and_hot_leads_first():
    items = sample_leads()
    rows = score_all(items, enrich([lead for lead, _ in items]), PROFILE)
    tiers = [s.tier for s in rows]
    assert set(tiers) == {"Hot", "Warm", "Nurture", "Route", "Duplicate", "Disqualified"}
    assert tiers == sorted(tiers, key=["Hot", "Warm", "Nurture", "Route", "Duplicate", "Disqualified"].index)
    by_id = {s.lead.id: s for s in rows}
    assert by_id["L007"].tier == "Disqualified"  # the prompt-injection spam
    assert by_id["L001"].tier == "Hot"
    assert by_id["L010"].tier == "Nurture"


def test_sample_services_exist_in_profile():
    names = {s.name for s in PROFILE.services}
    for _, r in sample_leads():
        assert r.matched_service in names | {None}
