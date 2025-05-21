import os
import pytest
import zipfile
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language

from beaker_kernel.lib.code_analysis.analyzer import CodeAnalyzer
from beaker_kernel.lib.code_analysis.rules import assumptions, groundings
from beaker_kernel.lib.code_analysis.analysis_types import AnalysisCodeCell, AnalysisCodeCells

solar_flare_nb = AnalysisCodeCells([
    AnalysisCodeCell(
        cell_id="solar_flare_nb-c1",
        notebook_id="solar_flare_nb",
        content="""\
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
    )
])

epa_eqs_nb = AnalysisCodeCells([
    AnalysisCodeCell(
        cell_id="epa_eqs_nb-c1",
        notebook_id="epa_eqs_nb",
        content="""\
import os
import requests
import pandas as pd
from datetime import datetime

# Get API credentials from environment variables
email = os.environ.get("API_EPA_AQS_EMAIL")
api_key = os.environ.get("API_EPA_AQS")

# Print credential status (not the actual values)
print(f"Email credential available: {email is not None}")
print(f"API key available: {api_key is not None}")

# Define parameters
base_url = "https://aqs.epa.gov/data/api"
state_code = "48"  # Texas
county_code = "201"  # Harris County
param_code = "44201"  # Ozone
year = 2022
month = 1

# Format dates
bdate = f"{year}{month:02d}01"  # First day of January 2022
edate = f"{year}{month:02d}31"  # Last day of January 2022

# Define constants
empty_weight_kg = 34400  # Empty weight of C-130 Hercules in kg
empty_weight_lbs = empty_weight_kg * 2.20462  # Convert kg to lbs

# Assuming the aircraft lands on all four wheels, we need to estimate the contact area.
# Let's assume each wheel has a contact area of 1 square foot (a rough estimate).
contact_area_per_wheel_sqft = 1  # square feet

total_contact_area_sqft = 4 * contact_area_per_wheel_sqft  # Total contact area for 4 wheels

# Calculate pressure exerted by the aircraft on the ice
pressure_psi = empty_weight_lbs / total_contact_area_sqft


# Build request URL and parameters
url = f"{base_url}/dailyData/byCounty"
params = {
    "email": email,
    "key": api_key,
    "param": param_code,
    "bdate": bdate,
    "edate": edate,
    "state": state_code,
    "county": county_code
}

# Make API request
print(f"Making request to {url} with parameters: {params}")
response = requests.get(url, params=params)

# Process the response
print(f"Response status code: {response.status_code}")
if response.status_code == 200:
    data = response.json()

    # Print the header information
    print("\nAPI Response Header:")
    print(data["Header"][0])

    # Check if we got successful data
    if data["Header"][0]["status"] == "Success":
        # Convert to dataframe
        daily_data = pd.DataFrame(data["Data"])

        # Show the first few rows
        print("\nFirst 5 rows of data:")
        print(daily_data.head())

        # Show data shape
        print(f"\nTotal records: {daily_data.shape[0]}")

        # Show unique sites
        print(f"\nUnique monitoring sites: {daily_data['local_site_name'].nunique()}")
        print(daily_data['local_site_name'].unique())

        # Convert date strings to datetime objects
        daily_data["date_local"] = pd.to_datetime(daily_data["date_local"])

        # Create a month column
        daily_data["month"] = daily_data["date_local"].dt.month

        # Group by site and date to get daily averages for each site
        site_daily_avg = daily_data.groupby(["local_site_name", "date_local"])["arithmetic_mean"].mean().reset_index()

        # Calculate monthly average for each site
        site_monthly_avg = site_daily_avg.groupby(["local_site_name"])["arithmetic_mean"].mean().reset_index()
        site_monthly_avg = site_monthly_avg.rename(columns={"arithmetic_mean": "monthly_mean"})

        # Calculate overall monthly average across all sites
        monthly_avg = site_daily_avg["arithmetic_mean"].mean()

        # Print results
        print(f"\nOzone data for Harris County, TX - January {year}")
        print(f"Number of daily records: {len(daily_data)}")
        print(f"Number of monitoring sites: {len(site_monthly_avg)}")
        print(f"Overall monthly average: {monthly_avg:.4f} ppm")
        print("\nSite-specific monthly averages:")
        print(site_monthly_avg.sort_values("monthly_mean", ascending=False))
    else:
        print(f"API request failed: {data['Header'][0]['status']}")
        if "error" in data["Header"][0]:
            print(f"Error message: {data['Header'][0]['error']}")
else:
    print(f"HTTP request failed with status code {response.status_code}")
    print(response.text)
"""
    )
])


hercules_nb: AnalysisCodeCells = AnalysisCodeCells([
    AnalysisCodeCell(
        cell_id="nb1-c1",
        notebook_id="nb1",
        content="""\
# Let's search for the empty weight of a C-130 Hercules from a reliable source.
import requests
from bs4 import BeautifulSoup

# URL of a reliable source for aircraft specifications
url = "https://www.lockheedmartin.com/en-us/products/c130.html"

# Send a request to the website
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Extract the relevant information
# This is a placeholder for the actual extraction logic, as the structure of the page may vary
# For demonstration, let's assume we find the weight in a specific tag or class
empty_weight_info = soup.find_all(text=lambda text: "empty weight" in text.lower())

empty_weight_info
"""
    ),
    AnalysisCodeCell(
        cell_id="nb1-c2",
        notebook_id="nb1",
        content="""\
# Constants
empty_weight_kg = 34400  # Empty weight of C-130 Hercules in kg
empty_weight_lbs = empty_weight_kg * 2.20462  # Convert kg to lbs

# Assuming the aircraft lands on all four wheels, we need to estimate the contact area.
# Let's assume each wheel has a contact area of 1 square foot (a rough estimate).
contact_area_per_wheel_sqft = 1  # square feet

total_contact_area_sqft = 4 * contact_area_per_wheel_sqft  # Total contact area for 4 wheels

# Calculate pressure exerted by the aircraft on the ice
pressure_psi = empty_weight_lbs / total_contact_area_sqft
pressure_psi
"""
    ),
    AnalysisCodeCell(
        cell_id="nb1-c3",
        notebook_id="nb1",
        content="""\
# Bearing strength of sea ice in psi
bearing_strength_psi = 500  # A typical safe estimate for sea ice

# Calculate the required ice thickness
# The thickness is proportional to the pressure exerted divided by the bearing strength
required_ice_thickness = pressure_psi / bearing_strength_psi
required_ice_thickness
"""
    ),
])


async def test_multi_codecell():
    language = Language(tspython.language())
    analyzer = CodeAnalyzer(rules=[assumptions, groundings], language=language)
    result = await analyzer.analyze(hercules_nb)
    print(result)
    assert result
    assert False
