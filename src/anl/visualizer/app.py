import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from negmas.helpers.inout import load
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
    if st.sidebar.checkbox("Show Negotiation", value=True):
        negotiation = st.sidebar.selectbox("Negotiation", all_negotiations)
        if negotiation is None:
            return
        neg_path = base / tournament / "negotiations" / (negotiation + ".csv")
        results_path = base / tournament / "results" / (negotiation + ".json")
        parts = negotiation.split("_")
        scenario_name = parts[0]
        scenario = Scenario.load(base / tournament / "scenarios" / scenario_name)
        if scenario is None:
            return

        # first_type = "_".join(parts[1:3])
        # second_type = "_".join(parts[3:5])
        st.write(f"##### Negotiation:\n {negotiation}")
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
        if st.sidebar.checkbox("Show 2D Plot", value=True):
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
        if st.sidebar.checkbox("Show Negotiator Offers", value=True):
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
                simple_offers_view=st.sidebar.checkbox(
                    "Simple Offers View", value=False
                ),
            )
            st.pyplot(plt.gcf())

        if st.sidebar.checkbox("Show Results Details", value=True):
            st.write("Results for this Negotiation:")
            st.write(results)

    if st.sidebar.checkbox("Plot Stats", value=False):
        metric = st.sidebar.multiselect("Metric", metrics, default=("advantage",))
        df = pd.read_csv(base / tournament / "all_scores.csv")
        if selected_scenarios:
            df = df.loc[df.scenario.isin(selected_scenarios), :]
        if type_:
            df = df.loc[df.strategy.isin(type_), :]
        st.dataframe(df)
        for m in metric:
            plt.figure()
            df.groupby(["strategy"])[m].plot(kind="kde", ylabel=m)
            plt.legend()
            plt.ylabel(m)
            st.pyplot(plt.gcf())


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TOURNAMENT_PATH)
