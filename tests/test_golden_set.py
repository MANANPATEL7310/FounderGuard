"""Golden Test Set: 15 diverse startup submissions verifying end-to-end model behavior."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.registry import registry

@pytest.fixture(scope="module")
def client():
    if not registry.is_ready:
        registry.load_all()
    with TestClient(app) as c:
        yield c

GOLDEN_CASES = [
    {
        "id": "golden_01_funded_us_enterprise_ai",
        "description": "Funded US enterprise AI startup with full metrics",
        "input": {
            "idea_description": "Enterprise autonomous workflow orchestration platform powered by domain-specific LLMs for insurance underwriters.",
            "problem_statement": "Underwriters spend 65% of their working hours manually extracting unstructured policy data and comparing guidelines.",
            "target_customer": "Commercial insurance carriers with over 500 underwriters in North America.",
            "industry": "Artificial Intelligence / ML",
            "country": "USA",
            "state": "CA",
            "business_model": ["B2B", "SaaS"],
            "stage": "growing",
            "funding_raised": 4500000.0,
            "currency": "USD",
            "funding_rounds": 2,
            "investor_types": ["venture capital", "angel"],
            "rounds_reached": ["Round A"],
            "team_size": 14,
            "team_skills": ["engineering", "product", "sales and marketing"],
            "founder_experience": "prior exit",
            "validation_evidence": "18 enterprise insurance clients live with annual contracts averaging $120k ARR.",
            "homepage_url": "https://underwriteai.com",
            "city": "San Francisco",
            "region": "SF Bay Area",
            "founded_at": "2021-01-15",
            "first_funding_at": "2021-06-01",
            "last_funding_at": "2022-10-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_02_prefunding_idea_us",
        "description": "Pre-funding US idea (0 funding, 0 rounds, dates missing)",
        "input": {
            "idea_description": "A collaborative peer-to-peer workspace renting network connecting remote freelancers with underutilized boutique hotel lounges.",
            "problem_statement": "Co-working spaces are expensive while hotel lounges sit completely empty on weekday mornings and afternoons.",
            "target_customer": "Digital nomads and freelancers who need quiet workspace without paying a monthly $400 desk subscription.",
            "industry": "Consumer Apps & Social",
            "country": "USA",
            "state": "NY",
            "business_model": ["Marketplace", "B2C"],
            "stage": "idea",
            "funding_raised": 0.0,
            "currency": "USD",
            "funding_rounds": 0,
            "investor_types": ["none"],
            "rounds_reached": ["none"],
            "team_size": 2,
            "team_skills": ["design", "product"],
            "founder_experience": "first-time",
            "consent": True,
        },
        "expected": {
            "model_a_status": "not_applicable",
            "model_b_status": "not_applicable",
            "model_c_status": "ok",
            "model_d_status": "ok",
            "interpretation": "Insufficient basis",
        }
    },
    {
        "id": "golden_03_funded_non_us_fintech",
        "description": "Funded UK FinTech with GBP currency conversion",
        "input": {
            "idea_description": "Cross-border B2B treasury and currency hedging API for mid-market European exporters.",
            "problem_statement": "Exporters lose 2 to 4 percent in hidden FX spreads and manual reconciliation fees.",
            "target_customer": "European import/export businesses processing between 5M and 50M EUR annually.",
            "industry": "FinTech & Financial Services",
            "country": "GBR",
            "business_model": ["B2B", "Transactional"],
            "stage": "launched",
            "funding_raised": 2000000.0,
            "currency": "GBP",
            "funding_rounds": 1,
            "investor_types": ["venture capital"],
            "rounds_reached": ["Round A"],
            "team_size": 8,
            "team_skills": ["engineering", "finance", "compliance"],
            "founder_experience": "domain veteran",
            "validation_evidence": "FCA sandbox authorization received and 8 corporate beta clients live.",
            "city": "London",
            "founded_at": "2020-03-01",
            "first_funding_at": "2020-09-01",
            "last_funding_at": "2020-09-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",  # runs with location warning
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_04_funded_us_missing_dates",
        "description": "Funded startup with missing dates (Model A not applicable, B runs)",
        "input": {
            "idea_description": "Automated clinical trial recruitment portal parsing electronic health records for oncology matches.",
            "problem_statement": "80% of clinical trials are delayed due to patient enrollment bottlenecks.",
            "target_customer": "Clinical research organizations (CROs) and principal investigators.",
            "industry": "Healthcare, Biotech & Life Sciences",
            "country": "USA",
            "state": "MA",
            "business_model": ["B2B", "SaaS"],
            "stage": "MVP",
            "funding_raised": 1800000.0,
            "currency": "USD",
            "funding_rounds": 1,
            "investor_types": ["venture capital"],
            "rounds_reached": ["Round A"],
            "team_size": 4,
            "team_skills": ["engineering", "domain expertise"],
            "founder_experience": "domain veteran",
            "founded_at": None,
            "first_funding_at": None,
            "last_funding_at": None,
            "consent": True,
        },
        "expected": {
            "model_a_status": "not_applicable",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_05_prefunding_healthcare_deep_validation",
        "description": "Pre-funding healthcare idea with high customer validation text",
        "input": {
            "idea_description": "AI acoustic sensor diagnosing pediatric respiratory infections from infant cough sounds via smartphone microphone.",
            "problem_statement": "Pediatricians lack rapid diagnostic tools for differentiating viral vs bacterial croup at home.",
            "target_customer": "Pediatric health networks and worried parents managing chronic asthma.",
            "industry": "Healthcare, Biotech & Life Sciences",
            "country": "USA",
            "state": "MA",
            "business_model": ["B2B2C", "SaaS"],
            "stage": "validation",
            "funding_raised": 0.0,
            "currency": "USD",
            "funding_rounds": 0,
            "team_size": 3,
            "team_skills": ["engineering", "domain expertise"],
            "founder_experience": "domain veteran",
            "validation_evidence": "Completed 120 doctor interviews and verified algorithm against 500 IRB-approved acoustic cough audio samples.",
            "consent": True,
        },
        "expected": {
            "model_a_status": "not_applicable",
            "model_b_status": "not_applicable",
            "model_c_status": "ok",
            "model_d_status": "ok",
            "interpretation": "Insufficient basis",
        }
    },
    {
        "id": "golden_06_funded_biotech_scaleup",
        "description": "Biotech startup with large funding and Series C milestone",
        "input": {
            "idea_description": "High-throughput microfluidic screening platforms discovering synthetic antibody therapeutics for autoimmune indications.",
            "problem_statement": "Traditional monoclonal antibody discovery requires 18 months per candidate with high attrition rates.",
            "target_customer": "Top 20 global pharmaceutical research organizations.",
            "industry": "Healthcare, Biotech & Life Sciences",
            "country": "USA",
            "state": "CA",
            "business_model": ["B2B", "Enterprise"],
            "stage": "growing",
            "funding_raised": 48000000.0,
            "currency": "USD",
            "funding_rounds": 4,
            "investor_types": ["venture capital"],
            "rounds_reached": ["Round A", "Round B", "Round C"],
            "team_size": 45,
            "team_skills": ["engineering", "domain expertise", "operations"],
            "founder_experience": "prior exit",
            "founded_at": "2018-05-01",
            "first_funding_at": "2018-11-01",
            "last_funding_at": "2022-03-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_07_temporal_drift_recent_year_2025",
        "description": "Funded startup with 2025 founding year triggering temporal warning",
        "input": {
            "idea_description": "Next-generation quantum-resistant cryptography key management for enterprise financial institutions.",
            "problem_statement": "Post-quantum migration mandates threaten legacy TLS and RSA cryptographic pipelines.",
            "target_customer": "Tier-1 retail and investment banks.",
            "industry": "Security & Cybersecurity",
            "country": "USA",
            "state": "NY",
            "business_model": ["B2B", "SaaS"],
            "stage": "launched",
            "funding_raised": 3500000.0,
            "currency": "USD",
            "funding_rounds": 1,
            "investor_types": ["venture capital"],
            "rounds_reached": ["Round A"],
            "team_size": 7,
            "team_skills": ["engineering", "security"],
            "founder_experience": "domain veteran",
            "founded_at": "2025-01-10",
            "first_funding_at": "2025-06-01",
            "last_funding_at": "2025-06-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_a_has_year_warning": True,
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_08_short_pitch_minimal",
        "description": "Minimal pitch triggering short-text warnings in C and D",
        "input": {
            "idea_description": "A mobile application for booking local dog walking and cat sitting appointments quickly.",
            "industry": "Consumer Apps & Social",
            "country": "USA",
            "state": "TX",
            "business_model": ["Marketplace"],
            "stage": "launched",
            "funding_raised": 250000.0,
            "currency": "USD",
            "funding_rounds": 1,
            "investor_types": ["angel"],
            "team_size": 2,
            "team_skills": ["engineering"],
            "founder_experience": "first-time",
            "founded_at": "2021-01-01",
            "first_funding_at": "2021-05-01",
            "last_funding_at": "2021-05-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_09_ecommerce_marketplace_traction",
        "description": "E-Commerce marketplace with established traction and metrics",
        "input": {
            "idea_description": "Curated consignment marketplace for authenticated luxury mechanical timepieces with escrow protection.",
            "problem_statement": "Counterfeit watches cause $1.8B in annual consumer fraud in secondhand transactions.",
            "target_customer": "Horology collectors and watch enthusiasts trading timepieces above $5,000.",
            "industry": "E-Commerce & Marketplaces",
            "country": "USA",
            "state": "CA",
            "business_model": ["Marketplace", "Transactional"],
            "stage": "growing",
            "funding_raised": 5000000.0,
            "currency": "USD",
            "funding_rounds": 2,
            "investor_types": ["venture capital", "angel"],
            "rounds_reached": ["Round A"],
            "team_size": 18,
            "team_skills": ["engineering", "operations", "marketing"],
            "founder_experience": "prior startup",
            "validation_evidence": "$14M GMV transacted over the past 12 months with 98% verified authentication rate.",
            "founded_at": "2019-04-01",
            "first_funding_at": "2019-10-01",
            "last_funding_at": "2021-04-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_10_cleantech_hardware_seed",
        "description": "German CleanTech hardware startup with Euro conversion",
        "input": {
            "idea_description": "Modular solid-state heat pumps reducing residential decarbonization installation costs by 50 percent.",
            "problem_statement": "Heat pump retrofits require costly hydronic modifications and specialized contractor labor.",
            "target_customer": "European residential heating contractors and municipal social housing providers.",
            "industry": "CleanTech & Energy",
            "country": "DEU",
            "business_model": ["Hardware", "B2B"],
            "stage": "MVP",
            "funding_raised": 850000.0,
            "currency": "EUR",
            "funding_rounds": 1,
            "investor_types": ["angel"],
            "team_size": 5,
            "team_skills": ["engineering", "domain expertise"],
            "founder_experience": "domain veteran",
            "founded_at": "2022-02-01",
            "first_funding_at": "2022-07-01",
            "last_funding_at": "2022-07-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_11_buzzword_heavy_ai",
        "description": "Buzzword-heavy pitch testing Model C vague term detection",
        "input": {
            "idea_description": "Revolutionary cutting-edge disruptive next-gen AI-driven holistic platform that seamlessly transforms synergistic enterprise workflows.",
            "problem_statement": "Legacy tools lack world-class smart innovative synergy.",
            "industry": "Artificial Intelligence / ML",
            "country": "USA",
            "state": "CA",
            "business_model": ["SaaS"],
            "stage": "MVP",
            "funding_raised": 1000000.0,
            "currency": "USD",
            "funding_rounds": 1,
            "investor_types": ["angel"],
            "team_size": 3,
            "team_skills": ["engineering"],
            "founder_experience": "first-time",
            "founded_at": "2021-01-01",
            "first_funding_at": "2021-06-01",
            "last_funding_at": "2021-06-01",
            "consent": True,
        },
        "expected": {
            "model_c_vague_terms": True,
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_12_failure_pattern_cashflow_unit_economics",
        "description": "Failure story profile testing Model D unit economics and funding cashflow",
        "input": {
            "idea_description": "Ultra-fast 10-minute grocery delivery app burning capital rapidly on courier subsidies and warehouse rents.",
            "problem_statement": "Unsustainable unit economics: high customer acquisition cost and customer churn with low order margins.",
            "target_customer": "Urban consumers wanting groceries in 10 minutes.",
            "industry": "E-Commerce & Marketplaces",
            "country": "USA",
            "state": "CA",
            "business_model": ["B2C"],
            "stage": "launched",
            "funding_raised": 20000000.0,
            "currency": "USD",
            "funding_rounds": 2,
            "investor_types": ["venture capital"],
            "rounds_reached": ["Round A", "Round B"],
            "team_size": 60,
            "team_skills": ["operations", "marketing"],
            "founder_experience": "first-time",
            "founded_at": "2020-01-01",
            "first_funding_at": "2020-04-01",
            "last_funding_at": "2021-01-01",
            "consent": True,
        },
        "expected": {
            "model_d_predicted_categories": ["unit_economics_pricing"],
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_13_canadian_saas",
        "description": "Canadian SaaS startup with CAD currency conversion",
        "input": {
            "idea_description": "Compliance management software automating Canadian privacy and PIPEDA regulatory audits for fintechs.",
            "problem_statement": "Mid-sized fintechs face complex multi-jurisdictional compliance paperwork.",
            "target_customer": "Canadian fintech startups and neo-banks.",
            "industry": "B2B SaaS / Enterprise Software",
            "country": "CAN",
            "business_model": ["B2B", "SaaS"],
            "stage": "launched",
            "funding_raised": 1200000.0,
            "currency": "CAD",
            "funding_rounds": 1,
            "investor_types": ["angel"],
            "team_size": 6,
            "team_skills": ["engineering", "legal"],
            "founder_experience": "prior startup",
            "founded_at": "2021-06-01",
            "first_funding_at": "2021-12-01",
            "last_funding_at": "2021-12-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_14_indian_mobile_consumer",
        "description": "Indian consumer app with INR currency conversion",
        "input": {
            "idea_description": "Vernacular audio learning and micro-course mobile community for Tier-2 and Tier-3 Indian blue-collar workers.",
            "problem_statement": "Vocational learners lack high quality professional upskilling in their native regional languages.",
            "target_customer": "Aspiring tradespersons and delivery drivers in Indian regional cities.",
            "industry": "Education & EdTech",
            "country": "IND",
            "business_model": ["B2C", "Subscription"],
            "stage": "MVP",
            "funding_raised": 50000000.0,  # ~600,000 USD
            "currency": "INR",
            "funding_rounds": 1,
            "investor_types": ["venture capital"],
            "team_size": 10,
            "team_skills": ["product", "engineering", "content"],
            "founder_experience": "prior startup",
            "founded_at": "2021-02-01",
            "first_funding_at": "2021-08-01",
            "last_funding_at": "2021-08-01",
            "consent": True,
        },
        "expected": {
            "model_a_status": "ok",
            "model_b_status": "ok",
            "model_c_status": "ok",
            "model_d_status": "ok",
        }
    },
    {
        "id": "golden_15_prefunding_b2b_tools",
        "description": "Pre-funding developer tool idea (solo founder, 0 funding)",
        "input": {
            "idea_description": "Command-line microservice mocking and contract testing tool for distributed Golang microservices.",
            "problem_statement": "Engineers spend days setting up local Docker compose environments for integration tests.",
            "target_customer": "Backend software engineers and DevOps teams.",
            "industry": "B2B SaaS / Enterprise Software",
            "country": "USA",
            "state": "WA",
            "business_model": ["SaaS"],
            "stage": "idea",
            "funding_raised": 0.0,
            "currency": "USD",
            "funding_rounds": 0,
            "team_size": 1,
            "team_skills": ["engineering"],
            "founder_experience": "first-time",
            "consent": True,
        },
        "expected": {
            "model_a_status": "not_applicable",
            "model_b_status": "not_applicable",
            "model_c_status": "ok",
            "model_d_status": "ok",
            "interpretation": "Insufficient basis",
        }
    }
]

@pytest.mark.parametrize("case", GOLDEN_CASES, ids=[c["id"] for c in GOLDEN_CASES])
def test_golden_case(client, case):
    # 1. Validate endpoint check
    res_val = client.post("/v1/evaluations/validate", json=case["input"])
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["valid"] is True

    # 2. Submit evaluation
    res_sub = client.post("/v1/evaluations", json=case["input"])
    assert res_sub.status_code == 202
    eval_id = res_sub.json()["evaluation_id"]

    # 3. Retrieve report
    res_rep = client.get(f"/v1/evaluations/{eval_id}/report")
    assert res_rep.status_code == 200
    rep = res_rep.json()

    # 4. Verify 8 sections
    assert "sections" in rep
    assert len(rep["sections"]) == 8

    # 5. Verify model expectations
    exp = case["expected"]
    if "model_a_status" in exp:
        assert rep["models"]["model_a"]["status"] == exp["model_a_status"], f"Model A status mismatch in {case['id']}"
    if "model_b_status" in exp:
        assert rep["models"]["model_b"]["status"] == exp["model_b_status"], f"Model B status mismatch in {case['id']}"
    if "model_c_status" in exp:
        assert rep["models"]["model_c"]["status"] == exp["model_c_status"], f"Model C status mismatch in {case['id']}"
    if "model_d_status" in exp:
        assert rep["models"]["model_d"]["status"] == exp["model_d_status"], f"Model D status mismatch in {case['id']}"
    if "interpretation" in exp:
        assert rep["interpretation"]["category"] == exp["interpretation"], f"Interpretation mismatch in {case['id']}"
    if exp.get("model_a_has_year_warning"):
        assert any("2015" in w for w in rep["models"]["model_a"]["warnings"])
    if exp.get("model_c_vague_terms"):
        assert len(rep["models"]["model_c"]["data"]["vague_terms"]) > 0
    if exp.get("model_d_predicted_categories"):
        for cat in exp["model_d_predicted_categories"]:
            assert cat in rep["models"]["model_d"]["data"]["predicted_categories"]

    # 6. Verify prioritized template recommendations (Step 3)
    res_rec = client.get(f"/v1/evaluations/{eval_id}/recommendations")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["status"] == "complete"
    assert rec_data["is_fallback"] is True
    assert rec_data["generation_method"] == "template_playbook"
    assert len(rec_data["recommendations"]) > 0

    # Verify every recommendation satisfies the 7 plan fields and priority constraint
    for r in rec_data["recommendations"]:
        assert r["id"]
        assert r["issue_id"]
        assert r["identified_problem_or_risk"]
        assert r["why_it_matters_for_this_startup"]
        assert r["specific_action"]
        assert r["priority"] in ("High", "Medium", "Low")
        assert len(r["implementation_steps"]) >= 3
        assert r["expected_benefit"]
        assert r["validation_method"]
        assert len(r["playbook_refs"]) >= 1
        assert "guarantee" not in r["expected_benefit"].lower()

