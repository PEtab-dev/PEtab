import warnings
from os import path
from tempfile import TemporaryDirectory
import pytest
from petab.C import *
from petab.visualize import (plot_data_and_simulation,
                             plot_measurements_by_observable,
                             save_vis_spec)
import matplotlib.pyplot as plt


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
def simu_file_Fujita():
    return "doc/example/example_Fujita/Fujita_simulatedData.tsv"


@pytest.fixture
def data_file_Fujita_minimal():
    return "doc/example/example_Fujita/Fujita_measurementData_minimal.tsv"


@pytest.fixture
def visu_file_Fujita_small():
    return "doc/example/example_Fujita/Fujita_visuSpec_small.tsv"


@pytest.fixture
def visu_file_Fujita_wo_dsid():
    return "doc/example/example_Fujita/visuSpecs/Fujita_visuSpec_1.tsv"


@pytest.fixture
def visu_file_Fujita_minimal():
    return "doc/example/example_Fujita/visuSpecs/Fujita_visuSpec_mandatory.tsv"


@pytest.fixture
def visu_file_Fujita_empty():
    return "doc/example/example_Fujita/visuSpecs/Fujita_visuSpec_empty.tsv"


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


def test_visualization_small_visu_file_w_datasetid(data_file_Fujita,
                                                   condition_file_Fujita,
                                                   visu_file_Fujita_small):
    """
    Test: visualization spezification file only with few columns in
    particular datasetId
    (optional columns are optional)
    """
    plot_data_and_simulation(data_file_Fujita,
                             condition_file_Fujita,
                             visu_file_Fujita_small)


def test_visualization_small_visu_file_wo_datasetid(data_file_Fujita,
                                                    condition_file_Fujita,
                                                    visu_file_Fujita_wo_dsid):
    """
    Test: visualization spezification file only with few columns in
    particular no datasetId column
    (optional columns are optional)
    """
    plot_data_and_simulation(data_file_Fujita,
                             condition_file_Fujita,
                             visu_file_Fujita_wo_dsid)


def test_visualization_minimal_visu_file(data_file_Fujita,
                                         condition_file_Fujita,
                                         visu_file_Fujita_minimal):
    """
    Test: visualization spezification file only with mandatory column plotId
    (optional columns are optional)
    """
    plot_data_and_simulation(data_file_Fujita,
                             condition_file_Fujita,
                             visu_file_Fujita_minimal)


def test_visualization_empty_visu_file(data_file_Fujita,
                                       condition_file_Fujita,
                                       visu_file_Fujita_empty):
    """
    Test: Empty visualization spezification file should default to routine
    for no file at all
    """
    plot_data_and_simulation(data_file_Fujita,
                             condition_file_Fujita,
                             visu_file_Fujita_empty)


def test_visualization_minimal_data_file(data_file_Fujita_minimal,
                                         condition_file_Fujita,
                                         visu_file_Fujita_small):
    """
    Test visualization, with the case: data file only with mandatory columns
    (optional columns are optional)
    """
    plot_data_and_simulation(data_file_Fujita_minimal,
                             condition_file_Fujita,
                             visu_file_Fujita_small)


def test_visualization_with_dataset_list(data_file_Isensee,
                                         condition_file_Isensee,
                                         simulation_file_Isensee):
    datasets = [['JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_ctrl',
                 'JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_Fsk'],
                ['JI09_160201_Drg453-452_CycNuc__ctrl',
                 'JI09_160201_Drg453-452_CycNuc__Fsk',
                 'JI09_160201_Drg453-452_CycNuc__Sp8_Br_cAMPS_AM']]
    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             dataset_id_list=datasets)

    plot_data_and_simulation(data_file_Isensee,
                             condition_file_Isensee,
                             sim_data=simulation_file_Isensee,
                             dataset_id_list=datasets)


def test_visualization_without_datasets(data_file_Fujita,
                                        condition_file_Fujita,
                                        simu_file_Fujita):
    sim_cond_num_list = [[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]]
    sim_cond_id_list = [['model1_data1'], ['model1_data2', 'model1_data3'],
                        ['model1_data4', 'model1_data5'], ['model1_data6']]
    observable_num_list = [[0], [1], [2], [0, 2], [1, 2]]
    observable_id_list = [['pS6_tot'], ['pEGFR_tot'], ['pAkt_tot']]

    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_cond_num_list=sim_cond_num_list,
                             plotted_noise=PROVIDED)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_data=simu_file_Fujita,
                             sim_cond_num_list=sim_cond_num_list,
                             plotted_noise=PROVIDED)

    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_cond_id_list=sim_cond_id_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_data=simu_file_Fujita,
                             sim_cond_id_list=sim_cond_id_list)

    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             observable_num_list=observable_num_list)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_data=simu_file_Fujita,
                             observable_num_list=observable_num_list)

    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             observable_id_list=observable_id_list,
                             plotted_noise=PROVIDED)
    plot_data_and_simulation(data_file_Fujita, condition_file_Fujita,
                             sim_data=simu_file_Fujita,
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
        assert(ErrMsg.args[0] == 'Either specify a list of simulation '
                                 'condition IDs or a list of simulation '
                                 'condition numbers, but not both. '
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

    # close open figures to avoid runtime warnings
    plt.close("all")

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


def test_save_plots_to_file(data_file_Isensee, condition_file_Isensee,
                            vis_spec_file_Isensee, simulation_file_Isensee):
    with TemporaryDirectory() as temp_dir:
        plot_data_and_simulation(
            data_file_Isensee,
            condition_file_Isensee,
            vis_spec_file_Isensee,
            simulation_file_Isensee,
            subplot_file_path=temp_dir)


def test_save_visu_file(data_file_Isensee,
                        condition_file_Isensee):

    with TemporaryDirectory() as temp_dir:
        save_vis_spec(data_file_Isensee,
                      condition_file_Isensee,
                      output_file_path=path.join(temp_dir, "visuSpec.tsv"))

        datasets = [['JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_ctrl',
                     'JI09_150302_Drg345_343_CycNuc__4_ABnOH_and_Fsk'],
                    ['JI09_160201_Drg453-452_CycNuc__ctrl',
                     'JI09_160201_Drg453-452_CycNuc__Fsk',
                     'JI09_160201_Drg453-452_CycNuc__Sp8_Br_cAMPS_AM']]

        save_vis_spec(data_file_Isensee,
                      condition_file_Isensee,
                      dataset_id_list=datasets,
                      output_file_path=path.join(temp_dir, "visuSpec1.tsv"))
