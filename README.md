# Taegis Parser Validator

A command-line tool to validate `.PAR` (parser) files against the Taegis API using the Taegis Python SDK.

## Description

This tool reads a parser file (`.PAR`) and validates its syntax and structure by calling the `validate_parser` endpoint from the Taegis Roadrunner service. It provides clear feedback on whether the parser is valid or contains errors, making it useful for:

- Validating parser code before deployment
- CI/CD pipeline integration
- Development and testing workflows
- Troubleshooting parser syntax issues

## Dependencies

### Required

- **Python 3.8 or higher**
- **taegis-sdk-python** - The official Taegis Python SDK

### Installation

1. Install the Taegis SDK:

```bash
pip install taegis-sdk-python
```

2. The script (`validate_parser.py`) should be in your working directory or on your PATH.

## Authentication

The tool supports multiple authentication methods:

### OAuth (Recommended)

Set the following environment variables:

```bash
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
```

**Windows (PowerShell):**
```powershell
$env:CLIENT_ID="your_client_id"
$env:CLIENT_SECRET="your_client_secret"
```

**Windows (Command Prompt):**
```cmd
set CLIENT_ID=your_client_id
set CLIENT_SECRET=your_client_secret
```

To generate a CLIENT_ID and CLIENT_SECRET, use the Taegis SDK:

```python
from taegis_sdk_python import GraphQLService

service = GraphQLService(environment="US1")
result = service.clients.mutation.create_client(name="my_app", roles=None)
print(f"CLIENT_ID: {result.client.client_id}")
print(f"CLIENT_SECRET: {result.client_secret}")
```

> **Important:** Store these credentials securely in an encrypted vault. Never commit them to version control.

### Device Code Authentication

If OAuth credentials are not provided, the tool will prompt for device code authentication. You'll be presented with a link to authenticate via the Taegis portal.

## Usage

### Basic Usage

Validate a parser file with default settings (parent_id=0, default environment):

```bash
python validate_parser.py my_parser.par
```

### Specify Environment

Validate against a specific Taegis environment:

```bash
python validate_parser.py my_parser.par --environment US1
python validate_parser.py my_parser.par --environment US2
python validate_parser.py my_parser.par -e EU
```

### Specify Parent Parser ID

If your parser is a child parser (not standalone), specify the parent parser ID:

```bash
python validate_parser.py my_parser.par --parent-id 123
python validate_parser.py my_parser.par -p 456
```

### Combined Options

```bash
python validate_parser.py my_parser.par --environment US1 --parent-id 0
```

## Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--environment` | `-e` | Taegis environment (US1, US2, US3, EU, charlie, delta, foxtrot, echo, production) | Default environment |
| `--parent-id` | `-p` | Parent parser ID (required by API) | `0` (standalone) |

### Environment Options

| Value | Alias | Endpoint |
|-------|-------|----------|
| `US1` | `charlie`, `production` | https://ctpx.secureworks.com/ |
| `US2` | `delta` | https://delta.taegis.secureworks.com/ |
| `US3` | `foxtrot` | https://foxtrot.taegis.secureworks.com/ |
| `EU` | `echo` | https://echo.taegis.secureworks.com/ |

## Output

The tool provides clear validation results:

### Valid Parser

```
Validating parser file: my_parser.par
Using parent_id: 0
Connecting to Taegis API...

============================================================
Validation Results:
============================================================
Status: ✓ VALID
Message: Parser validation successful
============================================================
```

### Invalid Parser

```
Validating parser file: my_parser.par
Using parent_id: 0
Connecting to Taegis API...

============================================================
Validation Results:
============================================================
Status: ✗ INVALID
Error: Syntax error at line 5: unexpected token
============================================================
```

## Exit Codes

- `0` - Parser is valid
- `1` - Parser is invalid or an error occurred

This makes the tool suitable for use in scripts and CI/CD pipelines:

```bash
#!/bin/bash
if python validate_parser.py my_parser.par; then
    echo "Parser is valid, proceeding with deployment"
    # ... deployment steps ...
else
    echo "Parser validation failed, aborting deployment"
    exit 1
fi
```

## Examples

### Example 1: Validate a Standalone Parser

```bash
python validate_parser.py standalone_parser.par
```

### Example 2: Validate a Child Parser

```bash
python validate_parser.py child_parser.par --parent-id 42
```

### Example 3: Validate Against US2 Environment

```bash
python validate_parser.py my_parser.par --environment US2
```

### Example 4: CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate Parser
  env:
    CLIENT_ID: ${{ secrets.TAEGIS_CLIENT_ID }}
    CLIENT_SECRET: ${{ secrets.TAEGIS_CLIENT_SECRET }}
  run: |
    python validate_parser.py parsers/my_parser.par --environment US1
```

## Error Handling

The tool handles various error scenarios:

- **File not found**: Clear error message if the `.PAR` file doesn't exist
- **Authentication errors**: Helpful guidance on setting up credentials
- **API errors**: Displays validation errors from the Taegis API
- **Network errors**: Reports connection issues

## Troubleshooting

### "Field 'parentId' of required type 'Int!' was not provided"

This error occurs if the API requires a parent_id. Ensure you're using the latest version of the script which includes the `--parent-id` parameter. If you're validating a standalone parser, use `--parent-id 0`.

### "Error: taegis-sdk-python is not installed"

Install the SDK:
```bash
pip install taegis-sdk-python
```

### Authentication Issues

1. Verify your `CLIENT_ID` and `CLIENT_SECRET` are set correctly
2. Check that your credentials have the necessary permissions
3. Try device code authentication if OAuth is not working

### Environment Not Found

Ensure you're using a valid environment identifier (US1, US2, US3, EU, or their aliases).

## Related Documentation

- [Taegis SDK for Python Documentation](https://code.8labs.io/platform/sdks/taegis_sdk_python)
- [Taegis API Authentication Guide](https://docs.ctpx.secureworks.com/apis/api_authenticate/)
- [Taegis Roadrunner Service](https://code.8labs.io/platform/sdks/taegis_sdk_python)

## License

This tool is provided as-is for use with the Taegis platform.

## Support

For issues related to:
- **This script**: Check the troubleshooting section or file an issue
- **Taegis SDK**: Refer to the SDK documentation
- **Taegis API**: Contact Taegis support
