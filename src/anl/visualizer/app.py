import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from negmas.helpers import distribute_integer_randomly
from negmas.helpers.inout import load, np
from negmas.inout import Scenario
from negmas.plots.util import TraceElement, plot_offline_run

from anl import DEFAULT_TOURNAMENT_PATH


def tournaments(base: Path = DEFAULT_TOURNAMENT_PATH):
    for mark in ("negotiations", "results", "scenarios"):
        path = base / mark
        if not (path.exists() and path.is_dir()):
            break
    else:
        return base.absolute().parent, [base.name]
    return base.absolute(), sorted([_.name for _ in base.glob("*") if _.is_dir()])


def negotiations(path: Path):
    base = path / "negotiations"
    return sorted(
        [_.stem for _ in base.glob("*") if _.is_file() and _.suffix.endswith("csv")]
    )


def read_scenarios(path: Path):
    base = path / "scenarios"
    return sorted([_.name for _ in base.glob("*") if _.is_dir()])


metrics = [
    "advantage",
    "kalai_optimality",
    "max_welfare_optimality",
    "nash_optimality",
    "pareto_optimality",
    "partner_welfare",
    "time",
    "utility",
    "welfare",
]


def run(base: Path = DEFAULT_TOURNAMENT_PATH):
    st.write("### ANL Tournament Visualizer")
    base, t = tournaments(base)
    tournament = st.sidebar.selectbox("Tournament", t)
    if tournament is None:
        return
    st.write(f"#### Tournament: {tournament}")
    scores = pd.read_csv(base / tournament / "scores.csv", index_col=0)
    scenarios = read_scenarios(base / tournament)
    scenario_prefix = st.sidebar.text_input("Scenario Prefix")
    selected_scenarios = st.sidebar.multiselect("Add Specific Scenarios", scenarios)
    prefix_selected = []
    if scenario_prefix:
        prefix_selected = [_ for _ in scenarios if _.startswith(scenario_prefix)]
    selected_scenarios = sorted(
        list(set(selected_scenarios).union(set(prefix_selected)))
    )
    types = sorted(scores["strategy"].unique().tolist())
    type_ = st.sidebar.multiselect("Strategies", types)
    if st.sidebar.checkbox("Show Final Scores", value=True):
        st.write("**Final Scores**")
        st.dataframe(scores)
    if st.sidebar.checkbox("Show Type Scores", value=False):
        st.write("**Type Scores**")
        metric = st.sidebar.multiselect("Metrics", metrics, default=("advantage",))
        df = pd.read_csv(
            base / tournament / "type_scores.csv", index_col=0, header=[0, 1]
        )
        if metric:
            df = df[[_ for _ in df.columns if _[0] in metric]]
        st.dataframe(df)

    if st.sidebar.checkbox("Show All Scores", value=False):
        st.write("**All Scores**")
        df = pd.read_csv(base / tournament / "all_scores.csv")
        if selected_scenarios:
            df = df.loc[df.scenario.isin(selected_scenarios), :]
        if type_:
            df = df.loc[df.strategy.isin(type_), :]
        st.dataframe(df)
    all_negotiations = negotiations(base / tournament)
    if selected_scenarios:
        all_negotiations = [
            _
            for _ in all_negotiations
            if any(_.startswith(x) for x in selected_scenarios)
        ]
    if type_:
        all_negotiations = [_ for _ in all_negotiations if any(x in _ for x in type_)]

    def display_negotiation(negotiation_set, neg_limits, indx=0, n_cols=1):
        n_negs = len(negotiation_set)
        for k in range(neg_limits[0], neg_limits[1]):
            negotiation = negotiation_set[k]
            st.write(negotiation)
            neg_path = base / tournament / "negotiations" / (negotiation + ".csv")
            results_path = base / tournament / "results" / (negotiation + ".json")
            parts = negotiation.split("_")
            scenario_name = parts[0]
            scenario = Scenario.load(base / tournament / "scenarios" / scenario_name)
            if scenario is None:
                return
            col1, col2 = st.columns(2)
            show_2d = show_offers = simple_offers = False
            with col1:
                side_by_side = st.checkbox(
                    "Side-by-Side",
                    value=n_cols == 1 and n_negs > 1,
                    key=f"side_by_side_{indx}_{k}",
                )
            with col2:
                show_details = st.checkbox(
                    "Outcome Details", value=False, key=f"results_{indx}_{k}"
                )
            if side_by_side:
                pass
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    show_2d = st.checkbox(
                        "2D Plot",
                        value=True,
                        key=f"twod_{indx}_{k}",
                    )
                with col2:
                    show_offers = st.checkbox(
                        "Offers",
                        value=n_cols == 1,
                        key=f"offer_{indx}_{k}",
                    )
                with col3:
                    if show_offers:
                        simple_offers = st.checkbox(
                            "Simple",
                            value=False,
                            key=f"simple_{indx}_{k}",
                        )

            # first_type = "_".join(parts[1:3])
            # second_type = "_".join(parts[3:5])
            trace_df = pd.read_csv(neg_path, index_col=None)
            trace = [
                TraceElement(
                    _[0],
                    _[1],
                    _[2],
                    _[3],
                    eval(_[4]),
                    {},
                    _[6],
                )
                for _ in trace_df.itertuples(index=False)
            ]
            results = load(results_path)
            if side_by_side:
                plot_offline_run(
                    trace,
                    ids=results["negotiator_ids"],
                    names=results["negotiator_names"],
                    ufuns=scenario.ufuns,  # type: ignore
                    agreement=results["agreement"],
                    broken=results["broken"],
                    has_error=results["has_error"],
                    timedout=results["timedout"],
                )
                st.pyplot(plt.gcf())
            else:
                if show_2d:
                    plot_offline_run(
                        trace,
                        ids=results["negotiator_ids"],
                        names=results["negotiator_names"],
                        ufuns=scenario.ufuns,  # type: ignore
                        agreement=results["agreement"],
                        broken=results["broken"],
                        has_error=results["has_error"],
                        timedout=results["timedout"],
                        only2d=True,
                    )
                    st.pyplot(plt.gcf())
                if show_offers:
                    plot_offline_run(
                        trace,
                        ids=results["negotiator_ids"],
                        names=results["negotiator_names"],
                        ufuns=scenario.ufuns,  # type: ignore
                        agreement=results["agreement"],
                        broken=results["broken"],
                        has_error=results["has_error"],
                        timedout=results["timedout"],
                        no2d=True,
                        simple_offers_view=simple_offers,
                    )
                    st.pyplot(plt.gcf())

            if show_details:
                st.write("Results for this Negotiation:")
                st.write(results)
        st.markdown("""---""")

    if st.sidebar.checkbox("Show Negotiation", value=True):
        negotiation_set = st.sidebar.multiselect("Negotiation", all_negotiations)
        n_cols = st.sidebar.slider("N. Columns", 1, 4, value=1)
        negs_for_col = distribute_integer_randomly(
            len(negotiation_set), n_cols, min_per_bin=None
        )
        negs_for_col = [_ for _ in negs_for_col if _]
        n_cols = len(negs_for_col)
        for i in range(1, n_cols):
            negs_for_col[i] += negs_for_col[i - 1]
        if n_cols:
            st.write(f"##### Negotiations")
            if n_cols == 1:
                display_negotiation(
                    negotiation_set, (0, len(negotiation_set)), n_cols=1
                )
            else:
                negs_for_col_limits = [(0, negs_for_col[0])] + list(
                    zip(negs_for_col[:-1], negs_for_col[1:])
                )
                cols = st.columns(n_cols)
                for indx, (col, neg_limits) in enumerate(
                    zip(cols, negs_for_col_limits)
                ):
                    with col:
                        if not neg_limits:
                            continue
                        display_negotiation(
                            negotiation_set, neg_limits, indx, n_cols=n_cols
                        )
    if st.sidebar.checkbox("Plot Stats", value=False):
        metric = st.sidebar.multiselect("Metric", metrics, default=("advantage",))
        df = pd.read_csv(base / tournament / "all_scores.csv")
        if selected_scenarios:
            df = df.loc[df.scenario.isin(selected_scenarios), :]
        if type_:
            df = df.loc[df.strategy.isin(type_), :]
        # st.dataframe(df)
        for m in metric:
            col1, col2, col3 = st.columns(3)

            with col1:
                show_table = st.checkbox(
                    "Show Table",
                    key=f"table_{m}",
                    value=True,
                )
                show_figs = st.checkbox(
                    "Show Graph",
                    key=f"graph_{m}",
                    value=True,
                )
            with col2:
                xvar = st.selectbox(
                    "X Variable", ("strategy", "scenario"), key=f"xvar_{m}"
                )
            if show_figs:
                with col3:
                    graph = st.selectbox(
                        "Graph Type",
                        ("violin", "box", "KDE", "histogram"),
                        key=f"graph_type_{m}",
                    )
                plt.figure()
                if graph == "violin":
                    sns.violinplot(df, x=xvar, y=m)
                if graph == "box":
                    sns.boxplot(df, x=xvar, y=m, notch=True)
                elif graph == "KDE":
                    df.groupby([xvar])[m].plot(kind="kde", ylabel=m)
                    plt.legend()
                elif graph == "histogram":
                    df.groupby([xvar])[m].plot(kind="hist", ylabel=m)
                    plt.legend()
                plt.ylabel(m)
                if len(df[xvar].unique()) > 6:
                    plt.xticks(rotation=90)
                st.pyplot(plt.gcf())
            if show_table:
                st.dataframe(df.groupby([xvar])[m].describe())


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TOURNAMENT_PATH)
