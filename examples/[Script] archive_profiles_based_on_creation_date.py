"""
Script to archive profiles from Hrflow.ai based on their creation date.
Packages to install :
    hrflow             (pypi): pip install hrflow

Usage:
    python script.py <api_secret> <api_user> <source_key> [--min_duration <years|months>]

Arguments:
    api_secret          (str): API secret key for Hrflow
    api_user            (str): API user for Hrflow
    source_key          (str): Source key for Hrflow profiles
    --min_duration      (str): Minimum duration to archive profiles (in years or months, e.g., '2y' or '6m')

Example:
    python script.py your_api_secret your_api_user your_source_key --min_duration 3y
    This will archive profiles created before 3 years ago.
    
    python script.py your_api_secret your_api_user your_source_key --min_duration 6m
    This will archive profiles created before 6 months ago.
    
    python script.py your_api_secret your_api_user your_source_key
    This will archive profiles created before 2 years ago (default).
"""

import argparse
import re
from hrflow import Hrflow
from hrflow.utils import get_all_profiles
from datetime import datetime, timezone

def calculate_duration_in_years(input_date):
    try:
        if input_date.endswith("Z"):
            input_date = input_date.replace("Z", "+0000")
        
        input_datetime = datetime.strptime(input_date, "%Y-%m-%dT%H:%M:%S%z")
        now = datetime.now(timezone.utc)
        duration_seconds = abs((now - input_datetime).total_seconds())
        decimal_years = duration_seconds / (365.25 * 24 * 3600)
        return round(decimal_years, 6)
    except Exception as e:
        print(f"Error: {str(e)}. Expected format: 'YYYY-MM-DDTHH:MM:SS[+0000|Z]'.")
        return 

def convert_to_decimal_years(period):
    """
    Convert period in 'Xy' for years or 'Xm' for months to decimal years.
    Example: '2y' -> 2.0, '6m' -> 0.5
    """
    match = re.match(r'(\d+)(y|m)', period.strip().lower())
    if not match:
        raise ValueError(f"Invalid period format: {period}. Use 'Xy' for years or 'Xm' for months.")
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 'y':
        return float(value)  # Directly return years as decimal years
    elif unit == 'm':
        return value / 12  # Convert months to years (e.g., 6 months = 0.5 years)

def archive_profiles(api_secret, api_user, source_key, min_duration):
    hrflow_client = Hrflow(api_secret=api_secret, api_user=api_user)
    profiles = get_all_profiles(hrflow_client, source_key=source_key)
    failed = []
    profiles_to_archive = []
    
    for profile in profiles:
        duration = calculate_duration_in_years(profile["created_at"])
        if duration and duration > min_duration:
            profiles_to_archive.append(profile)
    
    for profile in profiles_to_archive:
        response = hrflow_client.profile.storing.archive(source_key=source_key, key=profile["key"])
        if response["code"] != 200:
            print(f"Failed to archive profile with error: {response}")
            failed.append(profile)
    
    len_profiles_archived = len(profiles_to_archive) - len(failed)
    failed_keys = [profile["key"] for profile in failed]

    print(f"Number of profiles archived: {len_profiles_archived}")
    print(f"Failed profiles: {failed_keys}")

def main():
    parser = argparse.ArgumentParser(description="Script to archive profiles from Hrflow.ai based on their creation date.")
    parser.add_argument("api_secret", help="API secret key for Hrflow")
    parser.add_argument("api_user", help="API user for Hrflow")
    parser.add_argument("source_key", help="Source key for Hrflow profiles")
    parser.add_argument("--min_duration", type=str, default="2y", help="Minimum duration to archive profiles (in years or months, e.g., '2y' or '6m')")

    args = parser.parse_args()
    
    # Convert the 'min_duration' argument to decimal years
    min_duration_decimal = convert_to_decimal_years(args.min_duration)

    archive_profiles(args.api_secret, args.api_user, args.source_key, min_duration_decimal)

if __name__ == "__main__":
    main()