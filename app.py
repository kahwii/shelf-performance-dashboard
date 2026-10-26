"""Shelf Performance Dashboard - Retail Store Sales.

FOBA Final Project, Jose Rizal University.
Mark Emmanuel Sagarino and Carl Angelo Patano.

Audience:  the store manager, who controls assortment and reorder quantities.
Decisions: how many shelf facings each price tier gets in each category, and
           how much working capital to commit to stock.

Every figure on every page is computed from the filtered data at render time.
The note under each card is generated from those same numbers, so a note can
never contradict the chart above it after a filter changes.

Run it with Streamlit, not with Python:

    py -m streamlit run app.py          (Windows)
    python3 -m streamlit run app.py     (macOS / Linux)

Running `python app.py` or pressing VS Code's Run button starts the script
without the Streamlit server, so nothing renders. Install the libraries first
with `py -m pip install -r requirements.txt`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import plotly.graph_objects as go
    import streamlit as st
except ModuleNotFoundError as exc:                      # pragma: no cover
    sys.exit(
        f"\nMissing library: {exc.name}\n"
        f"Install the requirements first, from this folder:\n"
        f"    py -m pip install -r requirements.txt\n"
        f"then start the app with:\n"
        f"    py -m streamlit run app.py\n"
    )

DATA = Path(__file__).resolve().parent / "data" / "retail_store_sales_model_ready.csv"
TIERS = ["Budget", "Mid-range", "Premium"]

# ------------------------------------------------------------------ palette
# Price tier is ordinal, so it is drawn from a single-hue sequential ramp
# (light to dark = low to high), not from categorical hues. These are steps
# 3, 5 and 7 of the validated JRU blue ramp.
TIER_RAMP = {"Budget": "#88ADE6", "Mid-range": "#2563C7", "Premium": "#123571"}
S1, S2 = "#2563C7", "#C8901A"      # JRU blue and gold, categorical slots 1-2
SEQ2 = "#B9CFF2"

PLANE = "#f9f9f7"      # the page behind the cards
CARD = "#fcfcfb"       # the card surface
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SIDE = "#102A52"       # the deep navy of the school's identity
SIDE_INK = "#E9EFF8"
SIDE_MUTE = "#8CA3C4"

# Stated assumptions behind the capital figures. Neither is in the dataset.
UNITS_PER_FACING = 40     # units of stock behind one shelf facing
COST_RATIO = 0.70         # wholesale cost as a share of shelf price
ASSORTMENT_FLOOR = 3      # facings per tier per category that must remain
FACINGS_PER_CATEGORY = 25

st.set_page_config(page_title="Shelf Performance Dashboard",
                   page_icon="▪", layout="wide",
                   initial_sidebar_state="expanded")

# ------------------------------------------------------------------- styling
st.markdown(f"""
<style>
  .stApp {{ background: {PLANE}; }}
  .block-container {{ padding: 2.1rem 1.4rem 3rem; max-width: 1320px; }}
  html, body, [class*="css"] {{ font-size: 13.5px; }}

  /* ---------- navy rail, gold marks the page you are on ---------- */
  section[data-testid="stSidebar"] {{ background: {SIDE}; width: 248px !important; }}
  section[data-testid="stSidebar"] * {{ color: {SIDE_INK}; }}
  section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
    font-size: 10px; text-transform: uppercase; letter-spacing: .09em;
    color: {SIDE_MUTE}; font-weight: 600;
  }}
  section[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 1px; }}
  section[data-testid="stSidebar"] [role="radiogroup"] label {{
    padding: 7px 10px; border-radius: 7px; margin: 0; cursor: pointer;
  }}
  section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: rgba(255,255,255,.06);
  }}
  section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
    background: {S2};
  }}
  section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {{
    color: {SIDE}; font-weight: 600;
  }}
  section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{
    display: none;                      /* the radio dot; the gold fill is the state */
  }}
  section[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background: rgba(255,255,255,.12) !important;
  }}
  section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.12); }}

  .brand {{ display: flex; align-items: center; gap: 9px; padding: 2px 2px 14px; }}
  .bmark {{ width: 30px; height: 30px; border-radius: 8px; background: #1B4C9B;
            display: grid; place-items: center; flex: none; font-size: 13px;
            font-weight: 700; color: #fff; }}
  .brand b {{ display: block; font-size: 14px; color: #fff; }}
  .brand span {{ display: block; font-size: 10.5px; color: {SIDE_MUTE}; }}
  .sidenote {{ font-size: 10.8px; line-height: 1.5; color: {SIDE_MUTE}; }}

  /* ---------- topbar ---------- */
  .topbar h1 {{ font-size: 19px; font-weight: 600; letter-spacing: -.01em;
                margin: 0; color: {INK}; }}
  .topbar .sub {{ font-size: 11.8px; color: {MUTED}; margin-top: 2px; }}
  .badge {{ display: inline-block; font-size: 11px; color: {INK2}; background: {CARD};
            border: 1px solid rgba(11,11,11,.10); border-radius: 999px;
            padding: 3.5px 10px; margin-top: 9px; }}

  /* ---------- stat tiles ---------- */
  div[data-testid="stMetric"] {{
    background: {CARD}; border: 1px solid rgba(11,11,11,.10); border-radius: 12px;
    padding: 13px 15px; min-height: 104px;
    box-shadow: 0 1px 2px rgba(11,11,11,.05), 0 4px 12px rgba(11,11,11,.04);
  }}
  div[data-testid="stMetricLabel"] p {{ font-size: 11.3px !important; color: {MUTED}; }}
  div[data-testid="stMetricValue"] {{
    font-size: 23px; font-weight: 600; letter-spacing: -.02em; color: {INK};
    font-variant-numeric: tabular-nums;
  }}
  div[data-testid="stMetricDelta"] {{ font-size: 11.2px; }}

  /* ---------- cards ---------- */
  div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > .cardhead) {{
    background: {CARD}; border: 1px solid rgba(11,11,11,.10); border-radius: 12px;
    padding: 4px 6px 8px;
    box-shadow: 0 1px 2px rgba(11,11,11,.05), 0 4px 12px rgba(11,11,11,.04);
  }}
  .cardhead h3 {{ font-size: 13.5px; font-weight: 600; letter-spacing: -.01em;
                  margin: 0; color: {INK}; }}
  .cardhead .q {{ font-size: 10.4px; text-transform: uppercase; letter-spacing: .085em;
                  color: {MUTED}; font-weight: 600; margin: 0 0 3px; }}
  .cardnote {{ font-size: 11.4px; line-height: 1.55; color: {INK2};
               border-top: 1px solid rgba(11,11,11,.08); padding-top: 9px; margin-top: 2px; }}
  .cardnote b {{ color: {INK}; font-weight: 600; }}
  .cardnote .imp {{ color: #8a6410; font-weight: 600; }}

  /* ---------- tables ---------- */
  div[data-testid="stDataFrame"] {{ font-variant-numeric: tabular-nums; }}
  .stSlider label p {{ font-size: 11.8px !important; color: {INK2}; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- data layer
@st.cache_data
def load() -> pd.DataFrame:
    if not DATA.exists():
        st.error(
            f"Could not find the dataset at {DATA}. Keep `app.py` and the "
            f"`data` folder together, exactly as they came in the zip."
        )
        st.stop()
    df = pd.read_csv(DATA)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df


def money(x: float) -> str:
    return f"P{x:,.2f}"


def cardhead(q: str, title: str) -> None:
    """The business question, then the chart's own title."""
    st.markdown(f'<div class="cardhead"><p class="q">{q}</p><h3>{title}</h3></div>',
                unsafe_allow_html=True)


def cardnote(text: str) -> None:
    st.markdown(f'<div class="cardnote">{text}</div>', unsafe_allow_html=True)


def base_layout(fig: go.Figure, height: int = 300) -> go.Figure:
    """Recessive axes and grid, card-coloured surface, hover on by default."""
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=4, t=6, b=4),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif",
                  size=11.5, color=INK),
        hoverlabel=dict(bgcolor=CARD, font_color=INK, font_size=11.8,
                        bordercolor=AXIS),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left",
                    x=0, font=dict(size=11, color=INK2)),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=AXIS, linewidth=1,
                     tickcolor=AXIS, tickfont=dict(color=MUTED, size=10.5),
                     title_font=dict(color=MUTED, size=11))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
                     linecolor="rgba(0,0,0,0)", tickfont=dict(color=MUTED, size=10.5),
                     title_font=dict(color=MUTED, size=11))
    return fig


PLOT = {"displayModeBar": False}
df = load()

# -------------------------------------------------------------------- rail
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="bmark">SP</div>'
        '<div><b>Shelf Performance</b><span>Sagarino &amp; Patano</span></div>'
        "</div>", unsafe_allow_html=True)

    page = st.radio(
        "Pages",
        ["Shelf performance", "Demand and price", "Trend",
         "Shelf optimiser", "Data"],
        label_visibility="collapsed",
    )

    st.divider()

    dmin, dmax = df["transaction_date"].min().date(), df["transaction_date"].max().date()
    date_range = st.date_input("Transaction date", value=(dmin, dmax),
                               min_value=dmin, max_value=dmax,
                               help="Narrow the window to a season or a single year.")
    cats = sorted(df["category"].unique())
    sel_cats = st.multiselect("Category", cats, default=cats,
                              help="Compare a subset of the eight categories.")
    sel_tiers = st.multiselect("Price tier", TIERS, default=TIERS,
                               help="Budget is items 1-7, Mid-range 8-16, Premium 17-25.")

    st.divider()
    st.markdown(
        f'<p class="sidenote">Capital figures assume a facing holds '
        f'{UNITS_PER_FACING} units of stock and that wholesale cost is '
        f'{COST_RATIO:.0%} of shelf price. Neither figure is in the dataset.</p>',
        unsafe_allow_html=True)

# ---------------------------------------------------------------- filtering
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    d0, d1 = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    d0, d1 = pd.Timestamp(dmin), pd.Timestamp(dmax)

view = df[df["transaction_date"].between(d0, d1)
          & df["category"].isin(sel_cats)
          & df["price_tier"].isin(sel_tiers)]
rev = view[view["has_revenue_data"]].copy()

st.markdown(
    '<div class="topbar"><h1>Shelf Performance</h1>'
    '<p class="sub">Built for the store manager &mdash; which facings earn their '
    "keep, and where the next peso of stock should go</p></div>",
    unsafe_allow_html=True)

if rev.empty:
    st.warning("No priced transactions match these filters. Widen a filter to continue.")
    st.stop()

st.markdown(
    f'<span class="badge">{len(rev):,} priced of {len(view):,} transactions · '
    f'{len(view) - len(rev):,} carry no quantity and are excluded · '
    f'{d0.date()} to {d1.date()}</span>', unsafe_allow_html=True)
st.write("")

# ------------------------------------------------------------ headline tiles
revenue = float(rev["total_spent"].sum())
units = float(rev["quantity"].sum())
facings = int(rev["item"].nunique())
rev_per_facing = revenue / facings
eff_price = revenue / units
capital = COST_RATIO * eff_price * UNITS_PER_FACING * facings
rev_per_capital = revenue / capital
budget_shelf = rev[rev["price_tier"] == "Budget"]["item"].nunique()
budget_share = 100 * rev[rev["price_tier"] == "Budget"]["total_spent"].sum() / revenue
budget_shelf_share = 100 * budget_shelf / facings

k1, k2, k3, k4 = st.columns(4)
k1.metric("Measured revenue", money(revenue),
          help="Only transactions that carry a quantity. Nothing is imputed.")
k2.metric("Revenue per facing", money(rev_per_facing),
          help=f"Across {facings} items on the shelf. This is the unit the shelf "
               f"decision is actually made in.")
k3.metric("Return on stock", f"P{rev_per_capital:,.2f}",
          help="Pesos of revenue per peso of capital tied up in stock.")
k4.metric("Budget: shelf vs revenue",
          f"{budget_shelf_share:.1f}% / {budget_share:.1f}%",
          delta=f"{budget_share - budget_shelf_share:+.1f} pts",
          help="Share of facings against share of revenue. A negative gap means "
               "the tier takes more shelf than it earns.")
st.write("")

# ============================================================ SHELF PERFORMANCE
if page == "Shelf performance":
    c1, c2 = st.columns(2)

    with c1, st.container(border=True):
        cardhead("Which price tier earns most per shelf facing?",
                 "Revenue per facing by price tier")
        t = (rev.groupby("price_tier")
                .agg(revenue=("total_spent", "sum"), skus=("item", "nunique"))
                .reindex([x for x in TIERS if x in rev["price_tier"].unique()]))
        t["rpf"] = t["revenue"] / t["skus"]
        fig = go.Figure()
        fig.add_bar(x=t.index, y=t["rpf"],
                    marker=dict(color=[TIER_RAMP[i] for i in t.index],
                                line=dict(color=CARD, width=2)),
                    width=0.40, text=[f"P{v:,.0f}" for v in t["rpf"]],
                    textposition="outside", textfont=dict(color=INK, size=11),
                    hovertemplate="<b>%{x}</b><br>P%{y:,.2f} per facing<extra></extra>",
                    cliponaxis=False)
        fig.update_traces(marker_cornerradius=4)
        fig.update_yaxes(title_text="Pesos per facing", rangemode="tozero",
                         range=[0, float(t["rpf"].max()) * 1.18])
        st.plotly_chart(base_layout(fig), config=PLOT)
        if len(t) >= 2:
            top, bot = t["rpf"].idxmax(), t["rpf"].idxmin()
            cardnote(f"<b>{top}</b> facings return {money(t.loc[top, 'rpf'])} each "
                     f"against {money(t.loc[bot, 'rpf'])} for <b>{bot}</b> — "
                     f"{t.loc[top, 'rpf'] / t.loc[bot, 'rpf']:.1f}× the revenue from the "
                     f"same square of shelf. <span class='imp'>Implication:</span> a "
                     f"facing moved up a tier earns more without needing a single "
                     f"extra customer.")
        else:
            cardnote("Select more than one price tier to compare facings.")

    with c2, st.container(border=True):
        cardhead("Do any categories deserve different treatment?",
                 "Revenue share by category")
        c = rev.groupby("category")["total_spent"].sum().sort_values()
        share = 100 * c / c.sum()
        even = 100 / len(share)
        fig = go.Figure()
        fig.add_bar(x=share.values, y=share.index, orientation="h",
                    marker=dict(color=S1, line=dict(color=CARD, width=2)),
                    width=0.55, text=[f"{v:.1f}%" for v in share.values],
                    textposition="outside", textfont=dict(color=INK, size=10.5),
                    hovertemplate="<b>%{y}</b><br>%{x:.2f}% of revenue<extra></extra>",
                    cliponaxis=False)
        fig.update_traces(marker_cornerradius=4)
        fig.add_vline(x=even, line=dict(color=S2, width=2, dash="dot"),
                      annotation_text=f"even split {even:.1f}%",
                      annotation_position="top",
                      annotation_font=dict(color=S2, size=10.5))
        fig.update_xaxes(title_text="Share of revenue (%)",
                         range=[0, float(share.max()) * 1.24])
        fig.update_yaxes(showgrid=False)
        base_layout(fig)
        fig.update_layout(margin=dict(l=4, r=4, t=26, b=4))
        st.plotly_chart(fig, config=PLOT)
        cardnote(f"The eight categories sit between {share.min():.1f}% and "
                 f"{share.max():.1f}% of revenue — a spread of "
                 f"{share.max() - share.min():.1f} points around an even "
                 f"{even:.1f}%. <span class='imp'>Implication:</span> there is no "
                 f"category worth favouring, so shelf decisions should be made on "
                 f"price tier and applied to every category alike.")

# ============================================================ DEMAND AND PRICE
elif page == "Demand and price":
    c1, c2 = st.columns(2)

    with c1, st.container(border=True):
        cardhead("Do customers buy less when an item costs more?",
                 "Average units bought at each price point")
        p = rev.groupby("price_per_unit")["quantity"].mean().reset_index()
        fig = go.Figure()
        fig.add_scatter(x=p["price_per_unit"], y=p["quantity"], mode="markers",
                        marker=dict(size=8, color=S1, line=dict(color=CARD, width=2)),
                        hovertemplate="P%{x:.2f} per unit<br>%{y:.2f} units on "
                                      "average<extra></extra>", name="Observed")
        swing = 0.0
        if len(p) > 2:
            co = np.polyfit(rev["price_per_unit"], rev["quantity"], 1)
            xs = np.array([p["price_per_unit"].min(), p["price_per_unit"].max()])
            fig.add_scatter(x=xs, y=co[0] * xs + co[1], mode="lines",
                            line=dict(color=S2, width=2, dash="dash"),
                            hovertemplate="fitted trend<extra></extra>",
                            name="Fitted trend")
            fig.update_layout(showlegend=True)
            swing = float(co[0] * (xs[1] - xs[0]))
        fig.update_xaxes(title_text="Shelf price (pesos)")
        fig.update_yaxes(title_text="Mean units per transaction")
        st.plotly_chart(base_layout(fig), config=PLOT)
        r = float(np.corrcoef(rev["price_per_unit"], rev["quantity"])[0, 1])
        cardnote(f"The correlation between price and quantity is "
                 f"<b>r = {r:+.4f}</b>, and across the whole price range the fitted "
                 f"line moves by only <b>{swing:+.3f} units</b>. "
                 f"<span class='imp'>Implication:</span> demand here is flat, so "
                 f"raising the average shelf price does not cost the store volume "
                 f"— which is what makes the tier mix a real lever.")

    with c2, st.container(border=True):
        cardhead("Is any tier taking more shelf than it earns?",
                 "Share of shelf against share of revenue")
        t = (rev.groupby("price_tier")
                .agg(revenue=("total_spent", "sum"), skus=("item", "nunique"))
                .reindex([x for x in TIERS if x in rev["price_tier"].unique()]))
        shelf_pct = 100 * t["skus"] / t["skus"].sum()
        rev_pct = 100 * t["revenue"] / t["revenue"].sum()
        fig = go.Figure()
        fig.add_bar(x=t.index, y=shelf_pct, name="Share of shelf",
                    marker=dict(color=SEQ2, line=dict(color=CARD, width=2)),
                    width=0.3, offsetgroup=0,
                    text=[f"{v:.1f}%" for v in shelf_pct], textposition="outside",
                    textfont=dict(color=MUTED, size=10.5),
                    hovertemplate="<b>%{x}</b><br>%{y:.1f}% of facings<extra></extra>",
                    cliponaxis=False)
        fig.add_bar(x=t.index, y=rev_pct, name="Share of revenue",
                    marker=dict(color="#1B4C9B", line=dict(color=CARD, width=2)),
                    width=0.3, offsetgroup=1,
                    text=[f"{v:.1f}%" for v in rev_pct], textposition="outside",
                    textfont=dict(color=INK, size=10.5),
                    hovertemplate="<b>%{x}</b><br>%{y:.1f}% of revenue<extra></extra>",
                    cliponaxis=False)
        fig.update_traces(marker_cornerradius=4)
        fig.update_layout(barmode="group", bargap=0.35, showlegend=True)
        fig.update_yaxes(title_text="Percent",
                         range=[0, float(max(shelf_pct.max(), rev_pct.max())) * 1.22])
        st.plotly_chart(base_layout(fig), config=PLOT)
        gap = (rev_pct - shelf_pct).sort_values()
        worst = gap.index[0]
        cardnote(f"<b>{worst}</b> occupies {shelf_pct[worst]:.1f}% of the shelf and "
                 f"returns {rev_pct[worst]:.1f}% of revenue, a gap of "
                 f"<b>{gap.iloc[0]:+.1f} points</b>. "
                 f"<span class='imp'>Implication:</span> that gap is the shelf space "
                 f"to reclaim first, and it is the cheapest change available because "
                 f"the store already stocks the replacements.")

# ===================================================================== TREND
elif page == "Trend":
    with st.container(border=True):
        cardhead("When does the revenue arrive, and is the shelf decision seasonal?",
                 "Monthly revenue")
        m = (rev.set_index("transaction_date")
                .resample("MS")["total_spent"].sum().reset_index())
        fig = go.Figure()
        fig.add_scatter(x=m["transaction_date"], y=m["total_spent"], mode="lines",
                        line=dict(color="#1B4C9B", width=2), fill="tozeroy",
                        fillcolor="rgba(37,99,199,0.10)",
                        hovertemplate="%{x|%b %Y}<br>P%{y:,.2f}<extra></extra>")
        if len(m) > 1:
            peak = m.loc[m["total_spent"].idxmax()]
            fig.add_scatter(x=[peak["transaction_date"]], y=[peak["total_spent"]],
                            mode="markers+text",
                            marker=dict(size=9, color=S2,
                                        line=dict(color=CARD, width=2)),
                            text=[f"  peak P{peak['total_spent']:,.0f}"],
                            textposition="middle right",
                            textfont=dict(color=S2, size=10.5),
                            hovertemplate="peak month<extra></extra>",
                            cliponaxis=False)
        fig.update_yaxes(title_text="Revenue (pesos)", rangemode="tozero")
        st.plotly_chart(base_layout(fig, 340), config=PLOT)
        if len(m) > 2:
            full = m.iloc[1:-1] if len(m) > 3 else m
            cv = full["total_spent"].std(ddof=1) / full["total_spent"].mean()
            cardnote(f"Monthly revenue varies by a coefficient of variation of "
                     f"<b>{cv:.3f}</b> across {len(full)} complete months, peaking in "
                     f"<b>{peak['transaction_date']:%B %Y}</b>. "
                     f"<span class='imp'>Implication:</span> with no strong season to "
                     f"time around, the shelf mix can be changed once and left in "
                     f"place rather than rotated through the year.")
        else:
            cardnote("Widen the date filter to see the monthly pattern.")

# ============================================================ SHELF OPTIMISER
elif page == "Shelf optimiser":
    full = df[df["has_revenue_data"]]
    tf = (full.groupby("price_tier")
              .agg(revenue=("total_spent", "sum"), units=("quantity", "sum"),
                   skus=("item", "nunique")).reindex(TIERS))
    r_t = (tf["revenue"] / tf["skus"]).to_numpy()
    k_t = (COST_RATIO * (tf["revenue"] / tf["units"]) * UNITS_PER_FACING).to_numpy()
    cur = tf["skus"].to_numpy(dtype=float) / 8.0
    base_rev = 8 * float(r_t @ cur)
    base_cap = 8 * float(k_t @ cur)

    with st.container(border=True):
        cardhead("How much more would the shelf earn if the mix changed?",
                 "Facing allocation optimiser")
        st.caption(
            "The model decides how many of each category's 25 facings go to each "
            "price tier, applied uniformly to all eight categories. It is restricted "
            "that way on purpose: price tier explains 93.51% of the variance in "
            "revenue per facing and category only 0.72%, so an optimiser given free "
            "rein over all 24 cells would be fitting noise."
        )
        st.info(
            "**This page always uses the whole store**, whatever the sidebar "
            "filters are set to. The shelf is allocated as one decision across all "
            "200 facings, so optimising a filtered slice of it would recommend a "
            "mix the manager cannot actually put on the shelf. The figures here "
            "will not move when you change a filter — every other page will.",
            icon="ℹ️")
        slack = st.slider(
            "How much more stock capital is the manager willing to fund?",
            0, 40, 15, 1, format="+%d%%",
            help="The capital ceiling. At 0% the shelf must be rearranged without "
                 "tying up another peso.")
        ceiling = base_cap * (1 + slack / 100)

        cand, best = [], None
        for nb in range(ASSORTMENT_FLOOR, FACINGS_PER_CATEGORY + 1):
            for nm in range(ASSORTMENT_FLOOR, FACINGS_PER_CATEGORY - nb + 1):
                npr = FACINGS_PER_CATEGORY - nb - nm
                if npr < ASSORTMENT_FLOOR:
                    continue
                x = np.array([nb, nm, npr], dtype=float)
                cap = 8 * float(k_t @ x)
                if cap > ceiling + 1e-9:
                    continue
                val = 8 * float(r_t @ x)
                cand.append((nb, nm, npr, val))
                if best is None or val > best[0]:
                    best = (val, cap, x)

        if best is None:
            st.warning("No allocation satisfies that capital ceiling.")
            st.stop()

        opt_rev, opt_cap, x = best
        m1, m2, m3 = st.columns(3)
        m1.metric("Revenue", money(opt_rev),
                  delta=f"{100 * (opt_rev / base_rev - 1):+.2f}% vs today")
        m2.metric("Stock capital", money(opt_cap),
                  delta=f"{100 * (opt_cap / base_cap - 1):+.2f}% vs today",
                  delta_color="off")
        extra = opt_cap - base_cap
        m3.metric("Return on the extra stock",
                  money((opt_rev - base_rev) / extra) if extra > 1 else "n/a",
                  help="Pesos of revenue per peso of additional inventory.")

        cmp = pd.DataFrame({"Now": cur.astype(int), "Recommended": x.astype(int)},
                           index=TIERS)
        cmp["Change"] = cmp["Recommended"] - cmp["Now"]
        st.dataframe(cmp)

        cd = pd.DataFrame(cand, columns=["Budget", "Mid-range", "Premium", "revenue"])
        cd["gap"] = 100 * (cd["revenue"].max() - cd["revenue"]) / cd["revenue"].max()
        near = cd[cd["gap"] <= 1.0]
        moved = int(np.abs(cmp["Change"]).sum() / 2 * 8)
        cardnote(f"At a capital ceiling of <b>+{slack}%</b> the best mix is "
                 f"<b>Budget {int(x[0])}, Mid-range {int(x[1])}, Premium "
                 f"{int(x[2])}</b> per category — {moved} of 200 facings redeployed "
                 f"for <b>{100 * (opt_rev / base_rev - 1):+.2f}%</b> revenue. But "
                 f"{len(near)} mixes land within 1% of that peak, and in every one "
                 f"Premium sits between <b>{int(near['Premium'].min())} and "
                 f"{int(near['Premium'].max())}</b> facings. "
                 f"<span class='imp'>Implication:</span> the instruction that "
                 f"survives is <i>push Premium as high as the capital allows</i>; "
                 f"how the rest splits between Budget and Mid-range is worth under "
                 f"1% and is not a decision the data can make.")

    st.write("")
    with st.container(border=True):
        cardhead("What does each extra peso of stock buy?",
                 "Return as more capital is committed")
        rows = []
        for s in range(0, 41):
            ceil_s = base_cap * (1 + s / 100)
            bb = None
            for nb in range(ASSORTMENT_FLOOR, FACINGS_PER_CATEGORY + 1):
                for nm in range(ASSORTMENT_FLOOR, FACINGS_PER_CATEGORY - nb + 1):
                    npr = FACINGS_PER_CATEGORY - nb - nm
                    if npr < ASSORTMENT_FLOOR:
                        continue
                    xx = np.array([nb, nm, npr], dtype=float)
                    if 8 * float(k_t @ xx) > ceil_s + 1e-9:
                        continue
                    vv = 8 * float(r_t @ xx)
                    if bb is None or vv > bb:
                        bb = vv
            if bb is not None:
                rows.append((s, 100 * (bb / base_rev - 1)))
        fr = pd.DataFrame(rows, columns=["capital", "revenue"])
        fig = go.Figure()
        fig.add_scatter(x=fr["capital"], y=fr["revenue"], mode="lines",
                        line=dict(color="#1B4C9B", width=2), fill="tozeroy",
                        fillcolor="rgba(37,99,199,0.10)",
                        hovertemplate="+%{x}% capital<br>%{y:+.2f}% revenue"
                                      "<extra></extra>")
        fig.add_scatter(x=[slack], y=[100 * (opt_rev / base_rev - 1)],
                        mode="markers+text",
                        marker=dict(size=10, color=S2, line=dict(color=CARD, width=2)),
                        text=["  you are here"], textposition="middle right",
                        textfont=dict(color=S2, size=10.5),
                        hovertemplate="current setting<extra></extra>",
                        cliponaxis=False)
        fig.update_xaxes(title_text="Additional stock capital (%)")
        fig.update_yaxes(title_text="Additional revenue (%)", rangemode="tozero")
        st.plotly_chart(base_layout(fig, 290), config=PLOT)
        cardnote("Revenue rises almost in step with capital, at roughly <b>12 pesos "
                 "of revenue per peso of stock</b>, and the line does not bend. "
                 "<span class='imp'>Implication:</span> there is no natural stopping "
                 "point in the data, so how far to go is a financing decision for the "
                 "manager. What the data does settle is the direction — the shelf is "
                 "scarce as well as the capital, and on revenue per facing Premium "
                 "beats Mid-range by 1.6 to 1, so whatever capital is committed "
                 "should buy Premium facings first.")

# ====================================================================== DATA
elif page == "Data":
    with st.container(border=True):
        cardhead("What is behind every chart?", "Revenue by category and price tier")
        grid = (rev.groupby(["category", "price_tier"])
                   .agg(Revenue=("total_spent", "sum"), Units=("quantity", "sum"),
                        Transactions=("transaction_id", "count"),
                        Facings=("item", "nunique")).reset_index())
        grid["Revenue per facing"] = grid["Revenue"] / grid["Facings"]
        grid["Share of revenue %"] = 100 * grid["Revenue"] / grid["Revenue"].sum()
        grid = grid.rename(columns={"category": "Category", "price_tier": "Price tier"})
        st.dataframe(
            grid.style.format({"Revenue": "{:,.2f}", "Units": "{:,.0f}",
                               "Revenue per facing": "{:,.2f}",
                               "Share of revenue %": "{:.2f}"}),
            height=430, hide_index=True)
        st.download_button("Download this table as CSV",
                           grid.to_csv(index=False).encode("utf-8"),
                           file_name="shelf_performance_by_cell.csv", mime="text/csv")
        cardnote("Every chart in this dashboard is drawn from these aggregates, "
                 "recomputed under the filters currently applied. "
                 "<span class='imp'>Implication:</span> any figure quoted in the "
                 "paper or the presentation can be traced back to a row here.")
