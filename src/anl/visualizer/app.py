import sys
from collections import namedtuple
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


def is_tournament_folder(base: Path):
    if not base.is_dir():
        return False
    for mark in ("negotiations", "results", "scenarios"):
        path = base / mark
        if not (path.exists() and path.is_dir()):
            return False
    for mark in ("scores.csv", "type_scores.csv", "details.csv", "all_scores.csv"):
        path = base / mark
        if not (path.exists() and path.is_file()):
            return False
    return True


def tournaments(base: Path = DEFAULT_TOURNAMENT_PATH):
    if is_tournament_folder(base):
        return base.absolute().parent, [base.name]
    return (
        base.absolute(),
        sorted(
            [
                str(_.relative_to(base))
                for _ in base.glob("**/*")
                if is_tournament_folder(_)
            ]
        )[::-1],
    )


@st.cache_data
def negotiations(path: Path):
    base = path / "negotiations"
    return sorted(
        [_.stem for _ in base.glob("*") if _.is_file() and _.suffix.endswith("csv")]
    )


@st.cache_data
def read_scenarios(path: Path):
    base = path / "scenarios"
    return sorted([_.name for _ in base.glob("*") if _.is_dir()])


ScoreDataFrames = namedtuple(
    "ScoresDataFrame", ["final_scores", "type_scores", "all_scores", "details"]
)


@st.cache_resource
def read_score_dfs(
    base: Path,
    tournament: str,
    selected_scenarios: list[str] | None,
    selected_partners: list[str] | None,
    selected_strategies: list[str] | None,
    read_type: bool = True,
    read_all: bool = True,
    metric: str = "advantage",
    stat: str = "mean",
):
    if selected_strategies or selected_partners or selected_scenarios:
        read_all = True
    scores = pd.read_csv(base / tournament / "scores.csv", index_col=0)
    type_scores = (
        pd.read_csv(base / tournament / "type_scores.csv", index_col=0, header=[0, 1])
        if read_type
        else None
    )
    all_scores = pd.read_csv(base / tournament / "all_scores.csv") if read_all else None
    details = pd.read_csv(base / tournament / "details.csv")
    if selected_partners is not None:
        cond = details.negotiator_types.astype(bool)
        for p in selected_partners:
            cond &= details.negotiator_types.str.contains(p)
        details = details.loc[cond, :]
        assert all_scores is not None
        all_scores = all_scores.loc[all_scores.partners.isin(set(selected_partners)), :]
    if selected_strategies is not None:
        assert all_scores is not None
        cond = details.negotiator_types.astype(bool)
        for p in selected_strategies:
            cond &= details.negotiator_types.str.contains(p)
        details = details.loc[cond, :]
        all_scores = all_scores.loc[
            all_scores.strategy.isin(set(selected_strategies)), :
        ]
    if selected_scenarios is not None:
        assert all_scores is not None
        s = set(selected_scenarios)
        details = details.loc[(details.scenario.isin(s)), :]
        all_scores = all_scores.loc[
            all_scores.scenario.isin(set(selected_scenarios)), :
        ]
    if selected_scenarios or selected_partners or selected_strategies:
        assert all_scores is not None
        type_scores = all_scores.groupby(["strategy"]).describe()
        scores = type_scores[(metric, stat)]
    return ScoreDataFrames(scores, type_scores, all_scores, details)


def read_scenarios_with_steps(
    scenarios: list[str], details: pd.DataFrame
) -> dict[str, int]:
    n_scenarios_found = len(details.scenario.unique())
    n_scenarios = len(scenarios)
    assert (
        n_scenarios_found == n_scenarios
    ), f"Found {n_scenarios_found} scenarios in details but we should only find {n_scenarios}"
    min_n_steps = details.groupby(["scenario"])["n_steps"].min().rename("n_steps_min")  # type: ignore
    max_n_steps = details.groupby(["scenario"])["n_steps"].max().rename("n_steps_max")  # type: ignore
    all_n_steps = pd.concat(
        (min_n_steps, max_n_steps), axis=1, ignore_index=False, join="outer"
    )
    assert np.all(all_n_steps["n_steps_min"] == all_n_steps["n_steps_max"])
    return min_n_steps.to_dict()


@st.cache_resource
def make_scenario_stats(
    scenarios: list[str],
    details: pd.DataFrame,
    grouper: str | list[str] = "scenario",
    fields=(
        "n_steps",
        "time_limit",
        "n_repetitions",
        "step",
        "time",
        "relative_time",
        "broken",
        "timedout",
        "agreement_rate",
        "reserved_value(First)",
        "reserved_value(Second)",
        "execution_time",
        "pareto_optimality",
        "nash_optimality",
        "kalai_optimality",
        "modified_kalai_optimality",
        "max_welfare_optimality",
        "has_error",
    ),
) -> pd.DataFrame:
    if "DoneConversion" not in details.columns:
        for x in ("negotiator_types", "negotiator_ids", "negotiator_names"):
            if x in grouper:
                lst = [
                    ",".join(z.split(".")[-1] for z in eval(_))
                    for _ in details[x].to_list()
                ]
                details[x] = lst
        details["DoneConversion"] = True
    n_scenarios_found = len(details.scenario.unique())
    n_scenarios = len(scenarios)
    assert (
        n_scenarios_found == n_scenarios
    ), f"Found {n_scenarios_found} scenarios in details but we should only find {n_scenarios}"
    if isinstance(grouper, str):
        grouper = [grouper]  # type: ignore
    cols = grouper + list(fields)  # type: ignore
    details["agreement_rate"] = details.agreement.astype(str) != "nan"
    details["r"] = details.reserved_values.apply(lambda x: eval(x))
    details[["reserved_value(First)", "reserved_value(Second)"]] = pd.DataFrame(
        details["r"].tolist(), index=details.index
    )
    details = details[cols]  # type: ignore
    return details.groupby(grouper).mean()  # type: ignore


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
    st.set_page_config(
        page_title="your_title", layout="wide", initial_sidebar_state="auto"
    )
    st.write("### ANL Tournament Visualizer")
    base, t = tournaments(base)
    tournament = st.sidebar.selectbox("Tournament", t)
    if tournament is None:
        return
    st.write(f"#### Tournament: {tournament}")
    scenarios = read_scenarios(base / tournament)
    dfs = read_score_dfs(
        base,
        tournament,
        read_type=False,
        read_all=False,
        selected_partners=None,
        selected_scenarios=None,
        selected_strategies=None,
    )
    scores = dfs.final_scores
    steps_of = read_scenarios_with_steps(scenarios, dfs.details)
    # scenarios_of = dict(zip(steps_of.values(), steps_of.keys()))
    if st.sidebar.checkbox("Show Final Scores", value=True):
        st.write("**Final Scores**")
        st.dataframe(scores)
    with st.expander("Scenario Filter"):
        scenario_prefix = st.text_input("Scenario Prefix")
        selected_scenarios = st.multiselect("Specific Scenarios", scenarios)
        if not selected_scenarios:
            selected_scenarios = scenarios
        st.write("N. Steps")
        cola1, cola2 = st.columns(2)
        with cola1:
            selected_n_steps_min = st.number_input(
                label="min", min_value=1, key="min_n_steps", value=1
            )
        with cola2:
            selected_n_steps_max = st.number_input(
                label="max",
                min_value=selected_n_steps_min,
                value=1000_000,
                key="max_n_steps",
            )
        if selected_n_steps_max < selected_n_steps_min:
            st.write(
                "The maximum number of steps {selected_n_steps_max} is smaller than the minimum number {selected_n_steps_min}"
            )
            return
    with st.expander("Strategy Filter"):
        types = sorted(scores["strategy"].unique().tolist())
        type_ = st.multiselect("Strategies", types)
        partners = st.multiselect("Partners", types)
    prefix_selected = []
    if scenario_prefix:
        prefix_selected = [_ for _ in scenarios if _.startswith(scenario_prefix)]
    selected_scenarios = sorted(
        list(set(selected_scenarios).union(set(prefix_selected)))
    )
    # st.write(selected_scenarios)
    selected_scenarios = [
        _
        for _ in selected_scenarios
        if selected_n_steps_min <= steps_of[_] <= selected_n_steps_max
    ]
    st.write(
        f"Selected scenarios: {selected_scenarios if selected_scenarios  and len(selected_scenarios) < len(scenarios) else 'ALL'} and "
        f"Selected strategies: {type_ if type_ else 'ALL'} and "
        f"Selected partners: {partners if partners else 'ALL'}"
    )
    dfs = read_score_dfs(
        base,
        tournament,
        read_type=True,
        read_all=True,
        selected_partners=partners if partners else None,
        selected_scenarios=selected_scenarios if selected_scenarios else None,
        selected_strategies=type_ if type_ else None,
    )

    if st.sidebar.checkbox("Show Scenario Stats"):
        st.dataframe(make_scenario_stats(selected_scenarios, dfs.details))
    if st.sidebar.checkbox("Show Scenario x Strategy Stats"):
        st.dataframe(
            make_scenario_stats(
                selected_scenarios,
                dfs.details,
                grouper=["scenario", "negotiator_types"],
            )
        )
    if st.sidebar.checkbox("Show Cases Never Succeeding"):
        data = make_scenario_stats(
            selected_scenarios,
            dfs.details,
            grouper=["scenario", "negotiator_types"],
        )
        st.dataframe(data.loc[data.agreement_rate == 0, :])

    scores = dfs.final_scores
    st.write(f"Advantage (Score) for the selected set of scenarios and partners")
    st.dataframe(dfs.all_scores.groupby("strategy")["advantage"].describe())
    if st.sidebar.checkbox("Show Type Scores", value=False):
        st.write("**Type Scores**")
        metric = st.sidebar.multiselect("Metrics", metrics, default=("advantage",))
        df = dfs.type_scores
        if metric:
            df = df[[_ for _ in df.columns if _[0] in metric]]
        st.dataframe(df)

    if st.sidebar.checkbox("Show All Scores", value=False):
        st.write("**All Scores**")
        df = dfs.all_scores
        if selected_scenarios:
            df = df.loc[df.scenario.isin(selected_scenarios), :]
        if type_:
            df = df.loc[df.strategy.isin(type_), :]
        if partners:
            df = df.loc[df.partners.isin(partners), :]
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

    if partners:
        all_negotiations = [
            _ for _ in all_negotiations if any(x in _ for x in partners)
        ]

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
            x_var_offers = "relative_time"

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
                col1, col2, col3, col4 = st.columns(4)
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
                with col4:
                    if show_offers:
                        x_var_offers = st.selectbox(
                            "X-variable",
                            options=("relative_time", "time", "step"),
                            index=0,
                            key=f"xvar_offers_{indx}_{k}",
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
            names = [_.split(".")[-1] for _ in results["negotiator_names"]]
            if side_by_side:
                plot_offline_run(
                    trace,
                    ids=results["negotiator_ids"],
                    names=names,
                    ufuns=scenario.ufuns,  # type: ignore
                    agreement=results["agreement"],
                    broken=results["broken"],
                    has_error=results["has_error"],
                    timedout=results["timedout"],
                    ylimits=(0, 1),
                )
                st.pyplot(plt.gcf())
            else:
                if show_2d:
                    plot_offline_run(
                        trace,
                        ids=results["negotiator_ids"],
                        names=names,
                        ufuns=scenario.ufuns,  # type: ignore
                        agreement=results["agreement"],
                        broken=results["broken"],
                        has_error=results["has_error"],
                        timedout=results["timedout"],
                        only2d=True,
                        ylimits=(0, 1),
                    )
                    st.pyplot(plt.gcf())
                if show_offers:
                    plot_offline_run(
                        trace,
                        ids=results["negotiator_ids"],
                        names=names,
                        ufuns=scenario.ufuns,  # type: ignore
                        agreement=results["agreement"],
                        broken=results["broken"],
                        has_error=results["has_error"],
                        timedout=results["timedout"],
                        no2d=True,
                        simple_offers_view=simple_offers,
                        ylimits=(0, 1),
                        xdim=x_var_offers if x_var_offers else "relative_time",
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
            len(negotiation_set), n_cols, min_per_bin=None  # type: ignore
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
        if partners:
            df = df.loc[df.partners.isin(partners), :]
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
                xvar = st.multiselect(
                    "X Variable",
                    ("strategy", "scenario", "partners"),
                    key=f"xvar_{m}",
                    default=("strategy",),
                )
            if len(xvar) < 1:
                st.write(f"Choose some variable to analyze")
            # elif len(xvar) > 2:
            #     st.write(
            #         f"You selected {len(xvar)} variables for analysis. We only support up to two."
            #     )
            else:
                if show_figs:
                    with col3:
                        graph = st.selectbox(
                            "Graph Type",
                            ("violin", "box", "KDE", "histogram"),
                            key=f"graph_type_{m}",
                        )
                    plt.figure()

                    if len(xvar) > 2:
                        newcol = "(" + ", ".join(xvar[1:]) + ")"
                        df[newcol] = df[xvar[1]]
                        for i in range(2, len(xvar)):
                            df[newcol] += ", " + df[xvar[i]]
                    elif len(xvar) == 2:
                        newcol = xvar[1]
                    else:
                        newcol = None
                    if graph == "violin":
                        sns.violinplot(df, x=xvar[0], y=m, hue=newcol)
                    if graph == "box":
                        sns.boxplot(
                            df,
                            x=xvar[0],
                            y=m,
                            hue=newcol,
                            notch=True,
                        )
                    elif graph == "KDE":
                        df.groupby(xvar)[m].plot(kind="kde", ylabel=m)
                        plt.legend()
                    elif graph == "histogram":
                        df.groupby(xvar)[m].plot(kind="hist", ylabel=m)
                        plt.legend()
                    plt.ylabel(m)
                    if len(xvar) > 1 or (
                        len(xvar) == 1 and len(df[xvar[0]].unique()) > 6
                    ):
                        plt.xticks(rotation=90)
                    st.pyplot(plt.gcf())
                    plt.close()
                if show_table:
                    st.dataframe(df.groupby(xvar)[m].describe())
    if st.sidebar.checkbox("Negotiation Distributions", value=False):
        vars = [
            "n_steps",
            "time_limit",
            "step",
            "has_error",
            "relative_time",
            "time",
            "n_repetitions",
        ]
        # index,running,waiting,started,step,time,relative_time,broken,timedout,agreement,results,n_negotiators,has_error,error_details,threads,last_thread,current_offer,current_proposer,current_proposer_agent,
        # n_acceptances,new_offers,new_offerer_agents,last_negotiator,utilities,max_utils,reserved_values,partners,params,scenario,run_id,execution_time,negotiator_names,negotiator_ids,
        # negotiator_types,negotiator_times,n_steps,time_limit,pend,pend_per_second,step_time_limit,negotiator_time_limit,annotation,mechanism_name,mechanism_type,effective_scenario_name,rep,
        # n_repetitions,pareto_optimality,nash_optimality,kalai_optimality,modified_kalai_optimality,max_welfare_optimality,__weakref__
        scenario_vars = st.sidebar.multiselect(
            "Variable", vars, default=("n_steps",), key="dist_key"
        )
        df = dfs.details
        for v in scenario_vars:
            plt.figure()
            df[v].plot(kind="hist")
            st.pyplot(plt.gcf())
            plt.close()


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TOURNAMENT_PATH)
