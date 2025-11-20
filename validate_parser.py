#!/usr/bin/env python3
"""
Command line tool to validate a .PAR file against the Taegis API.

This tool uses the Taegis SDK to validate parser files (.PAR) by calling
the validate_parser endpoint from the Roadrunner service.

Usage:
    python validate_parser.py <path_to_par_file>
    
Environment Variables:
    CLIENT_ID: Taegis API client ID (required for OAuth authentication)
    CLIENT_SECRET: Taegis API client secret (required for OAuth authentication)
    
    Or the tool will prompt for device code authentication if OAuth is not configured.
"""

import argparse
import sys
from pathlib import Path

try:
    from taegis_sdk_python import GraphQLService
    from taegis_sdk_python.services.roadrunner.types import UnvalidatedParserInput
except ImportError:
    print("Error: taegis-sdk-python is not installed.", file=sys.stderr)
    print("Please install it with: pip install taegis-sdk-python", file=sys.stderr)
    sys.exit(1)


def read_par_file(file_path: str) -> str:
    """Read the contents of a .PAR file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    if not path.is_file():
        print(f"Error: Path is not a file: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def validate_parser_file(par_file_path: str, environment: str = None, parent_id: int = 0) -> None:
    """Validate a .PAR file using the Taegis API."""
    # Read the .PAR file content
    parser_code = read_par_file(par_file_path)
    
    # Initialize the Taegis service
    try:
        if environment:
            service = GraphQLService(environment=environment)
        else:
            service = GraphQLService()
    except Exception as e:
        print(f"Error initializing Taegis service: {e}", file=sys.stderr)
        print("\nMake sure you have set CLIENT_ID and CLIENT_SECRET environment variables", file=sys.stderr)
        print("or are ready to authenticate via device code.", file=sys.stderr)
        sys.exit(1)
    
    # Create the parser input with required parent_id
    parser_input = UnvalidatedParserInput(code=parser_code, parent_id=parent_id)
    
    # Validate the parser
    try:
        print(f"Validating parser file: {par_file_path}")
        print(f"Using parent_id: {parent_id}")
        print("Connecting to Taegis API...")
        
        result = service.roadrunner.query.validate_parser(parser_input)
        
        # Display results
        print("\n" + "="*60)
        print("Validation Results:")
        print("="*60)
        
        if result.ok:
            print("Status: ✓ VALID")
            if result.message:
                print(f"Message: {result.message}")
        else:
            print("Status: ✗ INVALID")
            if result.message:
                print(f"Error: {result.message}")
        
        print("="*60)
        
        # Exit with appropriate code
        sys.exit(0 if result.ok else 1)
        
    except Exception as e:
        print(f"Error validating parser: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Validate a .PAR file against the Taegis API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_parser.py my_parser.par
  python validate_parser.py my_parser.par --environment US1
  python validate_parser.py my_parser.par --environment US2 --parent-id 0
  python validate_parser.py my_parser.par --parent-id 123

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
        'par_file',
        help='Path to the .PAR file to validate'
    )
    
    parser.add_argument(
        '--environment',
        '-e',
        help='Taegis environment (US1, US2, US3, EU, charlie, delta, foxtrot, echo, production)',
        default=None
    )
    
    parser.add_argument(
        '--parent-id',
        '-p',
        type=int,
        help='Parent parser ID (required by API, default: 0 for standalone parsers)',
        default=0
    )
    
    args = parser.parse_args()
    
    validate_parser_file(args.par_file, args.environment, args.parent_id)


if __name__ == '__main__':
    main()

