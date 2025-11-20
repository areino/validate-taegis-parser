#!/usr/bin/env python3
"""
Command line tool to export unparsed events from Taegis.

This tool queries unparsed events (generic schema) for a specified tenant,
aggregates them by sensor_id and sensor_type, allows the user to select
a log source, and exports the selected events to a file.

Usage:
    python export_unparsed_events.py <tenant_id> <output_file>
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.getLogger("taegis_sdk_python.utils").setLevel(logging.ERROR)


try:
    from taegis_sdk_python import GraphQLService
    from taegis_sdk_python.services.events.types import EventQueryOptions
except ImportError:
    print("Error: taegis-sdk-python is not installed.", file=sys.stderr)
    print("Please install it with: pip install taegis-sdk-python", file=sys.stderr)
    sys.exit(1)


def get_next_page(events_results: List) -> str:
    """Retrieve events next page indicator."""
    for result in events_results:
        if hasattr(result, 'next') and result.next:
            return result.next
    return None


def query_events(
    service: GraphQLService,
    query: str,
    tenant_id: str,
    max_rows: int = 1000
) -> List[Dict]:
    """Query events and return all rows from all pages."""
    options = EventQueryOptions(
        timestamp_ascending=True,
        page_size=1000,
        max_rows=max_rows,
        skip_cache=True,
        aggregation_off=False,
    )

    all_rows = []
    results = []

    # Initial query
    with service(tenant_id=tenant_id):
        result_list = service.events.subscription.event_query(
            query=query,
            options=options,
            metadata={"callerName": "export_unparsed_events"},
        )
        results.extend(result_list)

        # Collect rows from initial results
        for r in result_list:
            if r.result and r.result.rows:
                all_rows.extend(r.result.rows)

        # Paginate through remaining results
        next_page = get_next_page(result_list)
        while next_page:
            page_result_list = service.events.subscription.event_page(next_page)
            results.extend(page_result_list)

            for r in page_result_list:
                if r.result and r.result.rows:
                    all_rows.extend(r.result.rows)

            next_page = get_next_page(page_result_list)

    return all_rows


def aggregate_by_sensor(events: List[Dict]) -> Dict[Tuple[str, str], List[Dict]]:
    """Aggregate events by sensor_id and sensor_type."""
    aggregated = defaultdict(list)

    for event in events:
        # Handle None values and missing keys
        sensor_id = event.get('sensor_id') or 'unknown'
        sensor_type = event.get('sensor_type') or 'unknown'
        # Convert to string in case they're not already
        sensor_id = str(sensor_id) if sensor_id is not None else 'unknown'
        sensor_type = str(sensor_type) if sensor_type is not None else 'unknown'
        key = (sensor_id, sensor_type)
        aggregated[key].append(event)

    return dict(aggregated)


def display_aggregated_sources(aggregated: Dict[Tuple[str, str], List[Dict]]) -> None:
    """Display aggregated log sources with counts."""
    print("\n" + "="*80)
    print("Available Log Sources (sensor_id, sensor_type):")
    print("="*80)

    # Sort by count (descending) then by sensor_id
    sorted_sources = sorted(
        aggregated.items(),
        key=lambda x: (-len(x[1]), x[0][0], x[0][1])
    )

    for idx, ((sensor_id, sensor_type), events) in enumerate(sorted_sources, 1):
        count = len(events)
        print(f"{idx:3d}. sensor_id='{sensor_id}' sensor_type='{sensor_type}' - {count:,} events")

    print("="*80)


def select_log_source(aggregated: Dict[Tuple[str, str], List[Dict]]) -> Tuple[str, str]:
    """Prompt user to select a log source."""
    sorted_sources = sorted(
        aggregated.items(),
        key=lambda x: (-len(x[1]), x[0][0], x[0][1])
    )

    if not sorted_sources:
        print("No log sources found.", file=sys.stderr)
        sys.exit(1)

    while True:
        try:
            choice = input(f"\nSelect a log source (1-{len(sorted_sources)}) or 'q' to quit: ").strip()

            if choice.lower() == 'q':
                print("Exiting.")
                sys.exit(0)

            choice_num = int(choice)
            if 1 <= choice_num <= len(sorted_sources):
                selected_key = sorted_sources[choice_num - 1][0]
                sensor_id, sensor_type = selected_key
                print(f"\nSelected: sensor_id='{sensor_id}' sensor_type='{sensor_type}'")
                return sensor_id, sensor_type
            else:
                print(f"Please enter a number between 1 and {len(sorted_sources)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)


def export_events_to_file(events: List[Dict], output_file: str) -> None:
    """Export events to a text file, writing only the original_data field from each event, one per line."""
    output_path = Path(output_file)

    try:
        # Extract only the original_data field from each event and write one per line
        count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for event in events:
                original_data = event.get('original_data')
                if original_data is not None:
                    # Write the original_data as a single line
                    # Convert to string if it's not already
                    data_str = str(original_data)
                    f.write(data_str)
                    f.write('\n')
                    count += 1

        print(f"\n✓ Successfully exported {count:,} events (original_data only, one per line) to: {output_path.absolute()}")
    except Exception as e:
        print(f"Error writing to file {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Export unparsed events from Taegis by sensor_id and sensor_type",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_unparsed_events.py tenant123 events.json
  python export_unparsed_events.py tenant123 events.json --environment US1
  python export_unparsed_events.py tenant123 events.json --max-rows 50000

Authentication:
  The tool uses OAuth authentication via CLIENT_ID and CLIENT_SECRET
  environment variables. If these are not set, it will prompt for
  device code authentication.

Environment Options:
  US1, charlie, production  - https://ctpx.secureworks.com/
  US2, delta                  - https://delta.taegis.secureworks.com/
  US3, foxtrot                - https://foxtrot.taegis.secureworks.com/
  EU, echo                    - https://echo.taegis.secureworks.com/
        """
    )

    parser.add_argument(
        'tenant_id',
        help='Tenant ID to query events for'
    )

    parser.add_argument(
        'output_file',
        help='Output file path (JSON format)'
    )

    parser.add_argument(
        '--environment',
        '-e',
        help='Taegis environment (US1, US2, US3, EU, charlie, delta, foxtrot, echo, production)',
        default=None
    )

    parser.add_argument(
        '--max-rows',
        '-m',
        type=int,
        help='Maximum number of rows to retrieve (default: 1000)',
        default=1000
    )

    parser.add_argument(
        '--time-range',
        '-t',
        help='Time range for query (default: -1d)',
        default='-1d'
    )

    args = parser.parse_args()

    # Initialize the Taegis service
    try:
        if args.environment:
            service = GraphQLService(environment=args.environment)
        else:
            service = GraphQLService()
    except Exception as e:
        print(f"Error initializing Taegis service: {e}", file=sys.stderr)
        print("\nMake sure you have set CLIENT_ID and CLIENT_SECRET environment variables", file=sys.stderr)
        print("or are ready to authenticate via device code.", file=sys.stderr)
        sys.exit(1)

    # Step 1: Query unparsed events
    query = f"FROM generic EARLIEST={args.time_range}"
    print(f"Querying unparsed events for tenant: {args.tenant_id}")
    print(f"Query: {query}")
    print("This may take a while...")

    try:
        events = query_events(service, query, args.tenant_id, args.max_rows)
        print(f"\n✓ Retrieved {len(events):,} events")
    except Exception as e:
        print(f"Error querying events: {e}", file=sys.stderr)
        sys.exit(1)

    if not events:
        print("No events found for the specified tenant and time range.")
        sys.exit(0)

    # Step 2: Aggregate by sensor_id and sensor_type
    print("\nAggregating events by sensor_id and sensor_type...")
    aggregated = aggregate_by_sensor(events)

    # Step 3: Display aggregated sources
    display_aggregated_sources(aggregated)

    # Step 4: Get user selection
    sensor_id, sensor_type = select_log_source(aggregated)

    # Step 5: Query events for selected log source
    print(f"\nQuerying events for sensor_id='{sensor_id}' sensor_type='{sensor_type}'...")
    # Escape single quotes in sensor_id and sensor_type for CQL
    sensor_id_escaped = sensor_id.replace("'", "''")
    sensor_type_escaped = sensor_type.replace("'", "''")
    filtered_query = f"FROM generic WHERE sensor_id='{sensor_id_escaped}' AND sensor_type='{sensor_type_escaped}' EARLIEST={args.time_range}"

    try:
        selected_events = query_events(service, filtered_query, args.tenant_id, args.max_rows)
        print(f"✓ Retrieved {len(selected_events):,} events for selected log source")
    except Exception as e:
        print(f"Error querying selected events: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 6: Export to file
    export_events_to_file(selected_events, args.output_file)


if __name__ == '__main__':
    main()

