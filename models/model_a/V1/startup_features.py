import numpy as np
import pandas as pd

RAW_COLS = ['homepage_url', 'category_list', 'funding_total_usd', 'country_code', 'state_code',
            'region', 'city', 'funding_rounds', 'founded_at', 'first_funding_at', 'last_funding_at']

NUM_COLS = ['funding_rounds', 'funding_total', 'funding_total_log', 'funding_missing',
            'funding_per_round', 'founded_year', 'first_funding_year', 'last_funding_year',
            'years_to_first_funding', 'funding_span_years', 'n_categories', 'has_homepage']

CAT_COLS = ['country_code', 'state_code', 'region', 'city', 'primary_category']

FEATURE_COLS = NUM_COLS + CAT_COLS


def engineer_features(df):
    df = df.reindex(columns=RAW_COLS)
    out = pd.DataFrame(index=df.index)

    funding = pd.to_numeric(
        df['funding_total_usd'].astype(str).str.replace(r'[^0-9.]', '', regex=True),
        errors='coerce')
    rounds = pd.to_numeric(df['funding_rounds'], errors='coerce')

    out['funding_rounds'] = rounds
    out['funding_total'] = funding
    out['funding_total_log'] = np.log1p(funding)
    out['funding_missing'] = funding.isna().astype(int)
    out['funding_per_round'] = funding / rounds.replace(0, np.nan)

    founded = pd.to_datetime(df['founded_at'], errors='coerce')
    first = pd.to_datetime(df['first_funding_at'], errors='coerce')
    last = pd.to_datetime(df['last_funding_at'], errors='coerce')
    out['founded_year'] = founded.dt.year
    out['first_funding_year'] = first.dt.year
    out['last_funding_year'] = last.dt.year
    out['years_to_first_funding'] = (first - founded).dt.days / 365.25
    out['funding_span_years'] = (last - first).dt.days / 365.25

    cats = df['category_list'].fillna('').astype(str).str.strip('|')
    out['n_categories'] = cats.apply(lambda s: len([c for c in s.split('|') if c]))
    out['primary_category'] = cats.str.split('|').str[0].replace('', 'missing')
    out['has_homepage'] = df['homepage_url'].notna().astype(int)

    for c in ['country_code', 'state_code', 'region', 'city']:
        out[c] = df[c]
    for c in CAT_COLS:
        out[c] = out[c].fillna('missing').astype(str)

    num = out[NUM_COLS].astype(float).replace([np.inf, -np.inf], np.nan)
    out[NUM_COLS] = num
    return out[FEATURE_COLS]
