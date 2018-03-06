"""
Tests for aws_searcher.tasks
"""
from pathlib import Path
import typing
import csv
import json

import pytest

import aws_searcher.tasks as TASKS


@pytest.fixture(autouse=True)
def fake_data() -> typing.List[typing.Dict[str, str]]:
    """
    Fixture that returns list of dictionary "rows"

    Returns:
        List of dictionary rows
    """
    return [
        {'name': 'Aaron', 'age': '38'},
        {'name': 'Juan', 'age': '35'},
        {'name': 'Trudeau', 'age': '45'}
    ]

@pytest.fixture(autouse=True)
def tmp_path(tmpdir) -> Path:
    """
    Create Path wrapped tmpdir reference

    Args:
        tmpdir: PyTest

    Returns:
        Path reference to
    """
    return Path(str(tmpdir))


@pytest.fixture(autouse=True)
def json_relationship_dicts() -> dict:
    """
    A dictionary with child, parent, and stand-alone test json

    Returns:
        Returns dict of List of dicts
    """
    file_names = ['child', 'parent']

    resources = Path(__file__).parent / 'resources'

    json_dict = {'stand-alone': {}}

    for file in file_names:
        full_path = resources / (file + '.json')
        with full_path.open() as infile:
            json_dict[file] = json.load(infile)

    return json_dict


def data_reader(file: Path) -> typing.List[typing.Dict[str, str]]:
    """
    Helper function to read in flat file data

    Args:
        file: Path object for test output

    Returns:
        List of dictionary rows
    """
    with file.open() as infile:
        reader = csv.DictReader(infile)
        data = [row for row in reader]
    return data


def test_serialize_data_to_csv(tmpdir) -> typing.NoReturn:
    """
    Assert that the data writes to csv as expected

    Args:
        tmpdir: Pytest built-in fixture

    """
    tmpdir_path = tmp_path(tmpdir)

    TASKS.serialize_data_to_csv(fake_data(), tmpdir_path)
    TASKS.serialize_data_to_csv(fake_data(), tmpdir_path, 'txt')

    assert_data = fake_data()

    files = list(tmpdir_path.glob('*.*'))

    assert len(files) == 2

    for file in files:
        for count, row in enumerate(data_reader(file)):
            assert set(row.items()) == set(assert_data[count].items())


def test_serialize_data_to_json(tmpdir) -> typing.NoReturn:
    """
    Asser that serialize_data_to_json works as expected

    Args:
        tmpdir: PyTest built-in fixture

    """
    tmpdir_path = tmp_path(tmpdir)

    assert_data = fake_data()

    TASKS.serialize_data_to_json(fake_data(), tmpdir_path)

    file = list(tmpdir_path.glob('*.json'))[0]

    with file.open() as infile:
        data = json.load(infile)

    for count, row in enumerate(data):
        assert set(row.items()) == set(assert_data[count].items())


def test_flatten_item_attributes() -> typing.NoReturn:
    """
    Assert that a nested json object is flattened to a single level

    """
    test = {
        'profile':
            {
                'name': 'Aaron',
                'age': 38
            },
        'animal': {
            'value': 'owl'
        }
    }

    expected_result = {
        'profile_name': 'Aaron',
        'profile_age': 38,
        'animal': 'owl'
    }

    assert set(expected_result.items()) == set(TASKS.flatten_item_attributes(test).items())


def test_extract_relationships_from_json() -> typing.NoReturn:
    """
    Assert that extract_relationships_from_json

    """
    test_json = json_relationship_dicts()

    parent_extract = TASKS.extract_relationships_from_json('test', test_json['parent'])

    assert len(parent_extract) == 2
    assert list(set([extract['relationship'] for extract in parent_extract]))[0] == 'parent'

    child_extract = TASKS.extract_relationships_from_json('test', test_json['child'])

    assert len(child_extract) == 1
    assert child_extract[0]['relationship'] == 'child'

    stand_alone_extract = TASKS.extract_relationships_from_json('test', test_json['stand-alone'])

    assert len(stand_alone_extract) == 1
    assert stand_alone_extract[0]['relationship'] == 'stand-alone'


def test_grouper():
    """
    Assert that grouper functions as expected

    """
    test_list = list(range(13))

    groups = TASKS.grouper(5, test_list)

    assert groups[0] == [0, 1, 2, 3, 4]
    assert groups[1] == [5, 6, 7, 8, 9]
    assert groups[2] == [10, 11, 12]
