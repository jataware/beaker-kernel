import os
import pytest
import zipfile
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree, Point, Node

from beaker_kernel.lib.trust import *


CODE_SAMPLE_1 = """\
# This code will fetch solar flare data from NASA DONKI for the past year
import os
import requests
from datetime import datetime, timedelta

api_key = os.environ.get('API_NASA', "DEMO_KEY")

# Calculate date range (past year)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# Format dates for API
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# API URL
url = f"https://api.nasa.gov/DONKI/FLR?startDate={start_date_str}&endDate={end_date_str}&api_key={api_key}"

# Make API request
response = requests.get(url)

if response.status_code == 200:
    solar_flare_data = response.json()
else:
    solar_flare_data = None
    print(f"Failed to fetch data: {response.status_code}")
"""

# import inspect
# raise ValueError(inspect.getfile(TrustLinter))

@pytest.fixture()
def test_temp_path(tmp_path_factory):
    return Path(tmp_path_factory.mktemp("test"))

@pytest.fixture()
def chromadb_store_path(tmp_path_factory):
    return str(tmp_path_factory.mktemp("test"))

@pytest.fixture()
def test_data_path():
    return Path(__file__).parent / "data"

def test_ast_parse():
    code = CODE_SAMPLE_1
    language = Language(tspython.language())
    linter = TrustLinter([], language)
    # parsed_code = linter.parse_code(code)
    # assert isinstance(parsed_code, Tree)

    # root = parsed_code.root_node
    # assert isinstance(root, Node)
    # assert root.descendant_count == 192

    # assert root.start_point == (0, 0) and root.end_point == (26, 0)
    # comment_node, import_node = root.children[0:2]
    # assert comment_node.type == "comment"
    # assert import_node.type == "import_statement"
    # api_key_statement = root.child(4)
    # url_statement = root.child(9)

    # print(api_key_statement)
    # print(api_key_statement.children)
    # print(url_statement)
    # print(url_statement.children)

    # # print(parsed_code.walk())
    # cursor = parsed_code.walk()
    # print(cursor)
    # # print(cursor.)

    # print(list(enumerate(root.children)))
    # assert False
