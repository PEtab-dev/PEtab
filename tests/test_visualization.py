import warnings

import pytest
from petab.C import *
from petab.visualize import (plot_data_and_simulation,
                             plot_measurements_by_observable)


@pytest.fixture
def data_file_Fujita():
    return "doc/example/example_Fujita/Fujita_measurementData.tsv"


@pytest.fixture
def condition_file_Fujita():
    return "doc/example/example_Fujita/Fujita_experimentalCondition.tsv"


@pytest.fixture
def data_file_Fujita_wrongNoise():
    return "doc/example/example_Fujita/Fujita_measurementData_wrongNoise.tsv"


@pytest.fixture
def data_file_Fujita_nanData():
    return "doc/example/example_Fujita/Fujita_measurementData_nanData.tsv"


@pytest.fixture
def data_file_Isensee():
    return "doc/example/example_Isensee/Isensee_measurementData.tsv"


@pytest.fixture
def condition_file_Isensee():
    return "doc/example/example_Isensee/Isensee_experimentalCondition.tsv"


@pytest.fixture
def vis_spec_file_Isensee():
    return "doc/example/example_Isensee/Isensee_visualizationSpecification.tsv"


@pytest.fixture
def simulation_file_Isensee():
    return "doc/example/example_Isensee/Isensee_simulationData.tsv"


def test_visualization_with_vis_and_sim(data_file_Isensee,
                                        condition_file_Isensee,
                                        vis_spec_file_Isensee,
                                        simulation_file_Isensee):
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             vis_spec_file_Isensee,
                             simulation_file_Isensee)


def test_visualization_with_vis(data_file_Isensee,
                                condition_file_Isensee,
                                vis_spec_file_Isensee):
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             vis_spec_file_Isensee)


def test_visualization_with_dataset_list(data_file_Isensee,
                                         condition_file_Isensee):
    datasets = [['JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_ctrl',
                 'JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_Fsk'],
                ['JI09_160201_Drg453-452_CycNuc__ctrl',
                 'JI09_160201_Drg453-452_CycNuc__Fsk',
                 'JI09_160201_Drg453-452_CycNuc__Sp8_Br_cAMPS_AM']]
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             dataset_id_list=datasets)


def test_visualization_without_datasets(data_file_Fujita,
                                        condition_file_Fujita):
    sim_cond_num_list = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]]
    sim_cond_id_list = [['model1_data1'], ['model1_data2', 'model1_data3'],
                        ['model1_data4', 'model1_data5'], ['model1_data6']]
    observable_num_list = [[0], [1], [2], [0, 2], [1, 2]]
    observable_id_list = [['pS6_tot'], ['pEGFR_tot'], ['pAkt_tot']]

    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_cond_num_list=sim_cond_num_list,
                             plotted_noise=PROVIDED)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_cond_id_list=sim_cond_id_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             observable_num_list=observable_num_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             observable_id_list=observable_id_list,
                             plotted_noise=PROVIDED)


def test_visualization_omit_empty_datasets(data_file_Fujita_nanData,
                                           condition_file_Fujita):
    observable_num_list = [[0, 1]]
    plot_data_and_simulation(data_file_Fujita_nanData, condition_file_Fujita,
                             observable_num_list=observable_num_list)


def test_visualization_raises(data_file_Fujita,
                              condition_file_Fujita,
                              data_file_Fujita_wrongNoise):
    sim_cond_num_list = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]]
    sim_cond_id_list = [['model1_data1'], ['model1_data2', 'model1_data3'],
                        ['model1_data4', 'model1_data5'], ['model1_data6']]
    observable_num_list = [[0], [1], [2], [0, 2], [1, 2]]
    observable_id_list = [['pS6_tot'], ['pEGFR_tot'], ['pAkt_tot']]
    error_counter = 0

    # Combining simulation condition numbers and IDs should not be allowed
    try:
        plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                                 sim_cond_num_list=sim_cond_num_list,
                                 sim_cond_id_list=sim_cond_id_list)
    except NotImplementedError as ErrMsg:
        assert(ErrMsg.args[0] == 'Either specify a list of dataset IDs or a '
                                 'list of dataset numbers, but not both. '
                                 'Stopping.')
        error_counter += 1
    assert (error_counter == 1)

    # Combining observable numbers and IDs should not be allowed
    try:
        plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                                 observable_num_list=observable_num_list,
                                 observable_id_list=observable_id_list)
    except NotImplementedError as ErrMsg:
        assert(ErrMsg.args[0] == 'Either specify a list of observable IDs or '
                                 'a list of observable numbers, but not both. '
                                 'Stopping.')
        error_counter += 1
    assert (error_counter == 2)

    # Combining observable and simulation conditions numbers or IDs should not
    # be allowed
    try:
        plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                                 sim_cond_num_list=observable_num_list,
                                 observable_num_list=observable_num_list)
    except NotImplementedError as ErrMsg:
        assert(ErrMsg.args[0] == 'Plotting without visualization specification'
                                 ' file and datasetId can be performed via '
                                 'grouping by simulation conditions OR '
                                 'observables, but not both. Stopping.')
        error_counter += 1
    assert (error_counter == 3)
    try:
        plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                                 sim_cond_id_list=observable_id_list,
                                 observable_id_list=observable_id_list)
    except NotImplementedError as ErrMsg:
        assert(ErrMsg.args[0] == 'Plotting without visualization specification'
                                 ' file and datasetId can be performed via '
                                 'grouping by simulation conditions OR '
                                 'observables, but not both. Stopping.')
        error_counter += 1
    assert (error_counter == 4)

    # If no numerical noise is provided, it should not work to plot it
    try:
        plot_measurements_by_observable(data_file_Fujita_wrongNoise,
                                        condition_file_Fujita,
                                        plotted_noise='provided')
    except NotImplementedError as ErrMsg:
        assert(ErrMsg.args[0] == "No numerical noise values provided in the "
                                 "measurement table. Stopping.")
        error_counter += 1

    assert (error_counter == 5)


def test_visualization_warnings(data_file_Isensee, condition_file_Isensee):
    datasets = [['JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_ctrl',
                 'JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_Fsk'],
                ['JI09_160201_Drg453-452_CycNuc__ctrl',
                 'JI09_160201_Drg453-452_CycNuc__Fsk',
                 'JI09_160201_Drg453-452_CycNuc__Sp8_Br_cAMPS_AM']]
    sim_cond_num_list = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]]
    observable_num_list = [[0], [1], [2], [0, 2], [1, 2]]

    with warnings.catch_warnings(record=True) as warnMsg:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")
        # plotting with datasetIds and sim conditions should issue a warning
        plot_data_and_simulation(data_file_Isensee,
                                 condition_file_Isensee,
                                 dataset_id_list=datasets,
                                 sim_cond_num_list=sim_cond_num_list)

        # plotting with datasetIds and observables should issue a warning
        plot_data_and_simulation(data_file_Isensee,
                                 condition_file_Isensee,
                                 dataset_id_list=datasets,
                                 observable_num_list=observable_num_list)

        # plotting with datasetIds and observables and sim conditions should
        # issue a warning
        plot_data_and_simulation(data_file_Isensee,
                                 condition_file_Isensee,
                                 dataset_id_list=datasets,
                                 observable_num_list=observable_num_list,
                                 sim_cond_num_list=sim_cond_num_list)

        # plotting grouped by something else than datasetIds should issue a
        # warning if datasetsIDs would have been available
        plot_data_and_simulation(data_file_Isensee,
                                 condition_file_Isensee,
                                 sim_cond_num_list=sim_cond_num_list)

        # test correct number of warnings
        assert len(warnMsg) == 4

        # test that all warnings were indeed UserWarnings
        for i_warn in warnMsg:
            assert issubclass(i_warn.category, UserWarning)


def test_simple_visualization(data_file_Fujita, condition_file_Fujita):
    plot_measurements_by_observable(data_file_Fujita, condition_file_Fujita)
    plot_measurements_by_observable(data_file_Fujita, condition_file_Fujita,
                                    plotted_noise=PROVIDED)
