#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

import numpy as np
from ax.benchmark.benchmark_method import BenchmarkMethod
from ax.benchmark.benchmark_problem import (
    BenchmarkProblem,
    MultiObjectiveBenchmarkProblem,
    SingleObjectiveBenchmarkProblem,
)
from ax.benchmark.benchmark_result import AggregatedBenchmarkResult, BenchmarkResult
from ax.benchmark.problems.surrogate import (
    MOOSurrogateBenchmarkProblem,
    SOOSurrogateBenchmarkProblem,
)
from ax.core.experiment import Experiment
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from ax.modelbridge.registry import Models
from ax.models.torch.botorch_modular.surrogate import Surrogate
from ax.service.scheduler import SchedulerOptions
from ax.utils.common.constants import Keys
from ax.utils.testing.core_stubs import (
    get_branin_multi_objective_optimization_config,
    get_branin_optimization_config,
    get_branin_search_space,
)
from botorch.acquisition.monte_carlo import qNoisyExpectedImprovement
from botorch.models.gp_regression import SingleTaskGP
from botorch.test_functions.multi_objective import BraninCurrin
from botorch.test_functions.synthetic import Branin


def get_benchmark_problem() -> BenchmarkProblem:
    return BenchmarkProblem.from_botorch(
        test_problem_class=Branin, test_problem_kwargs={}, num_trials=4
    )


def get_single_objective_benchmark_problem(
    infer_noise: bool = True,
    num_trials: int = 4,
) -> SingleObjectiveBenchmarkProblem:
    return SingleObjectiveBenchmarkProblem.from_botorch_synthetic(
        test_problem_class=Branin,
        test_problem_kwargs={},
        num_trials=num_trials,
        infer_noise=infer_noise,
    )


def get_multi_objective_benchmark_problem(
    infer_noise: bool = True, num_trials: int = 4
) -> MultiObjectiveBenchmarkProblem:
    return MultiObjectiveBenchmarkProblem.from_botorch_multi_objective(
        test_problem_class=BraninCurrin,
        test_problem_kwargs={},
        num_trials=num_trials,
        infer_noise=infer_noise,
    )


def get_sobol_benchmark_method() -> BenchmarkMethod:
    return BenchmarkMethod(
        name="SOBOL",
        generation_strategy=GenerationStrategy(
            steps=[GenerationStep(model=Models.SOBOL, num_trials=-1)],
            name="SOBOL",
        ),
        scheduler_options=SchedulerOptions(
            total_trials=4, init_seconds_between_polls=0
        ),
    )


def get_soo_surrogate() -> SOOSurrogateBenchmarkProblem:
    surrogate = Surrogate(
        botorch_model_class=SingleTaskGP,
    )
    return SOOSurrogateBenchmarkProblem(
        name="test",
        search_space=get_branin_search_space(),
        optimization_config=get_branin_optimization_config(),
        num_trials=6,
        infer_noise=False,
        metric_names=[],
        get_surrogate_and_datasets=lambda: (surrogate, []),
        optimal_value=0.0,
    )


def get_moo_surrogate() -> MOOSurrogateBenchmarkProblem:
    surrogate = Surrogate(botorch_model_class=SingleTaskGP)
    return MOOSurrogateBenchmarkProblem(
        name="test",
        search_space=get_branin_search_space(),
        optimization_config=get_branin_multi_objective_optimization_config(),
        num_trials=10,
        infer_noise=False,
        metric_names=[],
        get_surrogate_and_datasets=lambda: (surrogate, []),
        maximum_hypervolume=1.0,
        reference_point=[],
    )


def get_sobol_gpei_benchmark_method() -> BenchmarkMethod:
    return BenchmarkMethod(
        name="MBO_SOBOL_GPEI",
        generation_strategy=GenerationStrategy(
            name="Modular::Sobol+GPEI",
            steps=[
                GenerationStep(model=Models.SOBOL, num_trials=3, min_trials_observed=3),
                GenerationStep(
                    model=Models.BOTORCH_MODULAR,
                    num_trials=-1,
                    model_kwargs={
                        "surrogate": Surrogate(SingleTaskGP),
                        # TODO: tests should better reflect defaults and not
                        # re-implement this logic.
                        "botorch_acqf_class": qNoisyExpectedImprovement,
                    },
                    model_gen_kwargs={
                        "model_gen_options": {
                            Keys.OPTIMIZER_KWARGS: {
                                "num_restarts": 50,
                                "raw_samples": 1024,
                            },
                            Keys.ACQF_KWARGS: {
                                "prune_baseline": True,
                            },
                        }
                    },
                ),
            ],
        ),
        scheduler_options=SchedulerOptions(
            total_trials=4, init_seconds_between_polls=0
        ),
    )


def get_benchmark_result() -> BenchmarkResult:
    problem = get_single_objective_benchmark_problem()

    return BenchmarkResult(
        name="test_benchmarking_result",
        seed=0,
        experiment=Experiment(
            name="test_benchmarking_experiment",
            search_space=problem.search_space,
            optimization_config=problem.optimization_config,
            runner=problem.runner,
            is_test=True,
        ),
        optimization_trace=np.array([3, 2, 1, 0.1]),
        score_trace=np.array([3, 2, 1, 0.1]),
        fit_time=0.1,
        gen_time=0.2,
    )


def get_aggregated_benchmark_result() -> AggregatedBenchmarkResult:
    result = get_benchmark_result()
    return AggregatedBenchmarkResult.from_benchmark_results([result, result])
