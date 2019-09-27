import os
from tempfile import TemporaryDirectory
from petab.visualize.data_overview import main


def test_data_overview():
    # Ensure report creation succeeds for Fujita example model
    outfile = 'Fujita.html'

    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        main()

        assert os.path.isfile(outfile)
