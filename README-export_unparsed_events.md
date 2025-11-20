# Taegis Unparsed Events Exporter

A command-line tool to query, aggregate, and export unparsed events from the Taegis platform using the Taegis Python SDK.

## Description

This tool queries unparsed events (events in the "generic" schema) for a specified tenant, aggregates them by `sensor_id` and `sensor_type`, allows interactive selection of a log source, and exports the selected events' `original_data` to a plain text file (one log entry per line).

Use cases:
- Analyzing unparsed log data for parser development
- Exporting sample logs from specific log sources
- Troubleshooting parsing issues
- Gathering test data for parser validation

## Dependencies

### Required

- **Python 3.8 or higher**
- **taegis-sdk-python** - The official Taegis Python SDK

### Installation

1. Install the Taegis SDK:

```bash
pip install taegis-sdk-python
```

2. The script (`export_unparsed_events.py`) should be in your working directory or on your PATH.

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

Query unparsed events for a tenant and export selected log source:

```bash
python export_unparsed_events.py tenant123 output.txt
```

### Specify Environment

Query against a specific Taegis environment:

```bash
python export_unparsed_events.py tenant123 output.txt --environment US1
python export_unparsed_events.py tenant123 output.txt --environment US2
python export_unparsed_events.py tenant123 output.txt -e EU
```

### Custom Time Range

Query events from a different time period:

```bash
python export_unparsed_events.py tenant123 output.txt --time-range -7d
python export_unparsed_events.py tenant123 output.txt -t -24h
```

### Limit Maximum Rows

Control the maximum number of events to retrieve:

```bash
python export_unparsed_events.py tenant123 output.txt --max-rows 5000
python export_unparsed_events.py tenant123 output.txt -m 10000
```

### Combined Options

```bash
python export_unparsed_events.py tenant123 output.txt --environment US1 --time-range -7d --max-rows 5000
```

## Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `tenant_id` | - | Tenant ID to query events for (required) | - |
| `output_file` | - | Output file path (required) | - |
| `--environment` | `-e` | Taegis environment (US1, US2, US3, EU, charlie, delta, foxtrot, echo, production) | Default environment |
| `--max-rows` | `-m` | Maximum number of rows to retrieve | `1000` |
| `--time-range` | `-t` | Time range for query (e.g., -1d, -7d, -24h) | `-1d` |

### Environment Options

| Value | Alias | Endpoint |
|-------|-------|----------|
| `US1` | `charlie`, `production` | https://ctpx.secureworks.com/ |
| `US2` | `delta` | https://delta.taegis.secureworks.com/ |
| `US3` | `foxtrot` | https://foxtrot.taegis.secureworks.com/ |
| `EU` | `echo` | https://echo.taegis.secureworks.com/ |

### Time Range Format

The `--time-range` option accepts relative time expressions:
- `-1d` - Last 24 hours
- `-7d` - Last 7 days
- `-24h` - Last 24 hours
- `-1h` - Last hour
- `-30m` - Last 30 minutes

## Workflow

The tool follows this workflow:

1. **Query Unparsed Events**: Queries events from the "generic" schema for the specified tenant and time range
2. **Aggregate by Log Source**: Groups events by `sensor_id` and `sensor_type` and counts events per group
3. **Display Available Sources**: Shows a numbered list of all log sources with event counts
4. **Interactive Selection**: Prompts you to select a log source by number
5. **Filtered Query**: Queries only events matching the selected `sensor_id` and `sensor_type`
6. **Export**: Writes the `original_data` field from each event to the output file (one per line)

## Output Format

The output file is a plain text file where each line contains the `original_data` field from one event. There is no JSON formatting or wrapper - just the raw log data, one entry per line.

Example output file:
```
<134>1 2024-01-15T10:30:45.123Z hostname app process - [meta] Log message here
<134>1 2024-01-15T10:30:46.456Z hostname app process - [meta] Another log message
<134>1 2024-01-15T10:30:47.789Z hostname app process - [meta] Yet another message
```

## Interactive Selection

When you run the tool, you'll see output like this:

```
Querying unparsed events for tenant: tenant123
Query: FROM generic EARLIEST=-1d
This may take a while...

✓ Retrieved 1,234 events

Aggregating events by sensor_id and sensor_type...

================================================================================
Available Log Sources (sensor_id, sensor_type):
================================================================================
  1. sensor_id='192.168.1.100' sensor_type='syslog' - 456 events
  2. sensor_id='192.168.1.101' sensor_type='syslog' - 321 events
  3. sensor_id='10.0.0.50' sensor_type='cef' - 234 events
  4. sensor_id='192.168.1.100' sensor_type='json' - 123 events
  5. sensor_id='10.0.0.51' sensor_type='syslog' - 100 events
================================================================================

Select a log source (1-5) or 'q' to quit: 
```

Enter the number corresponding to the log source you want to export, or `q` to quit.

## Examples

### Example 1: Basic Export

```bash
python export_unparsed_events.py tenant123 logs.txt
```

### Example 2: Export from Last Week

```bash
python export_unparsed_events.py tenant123 logs.txt --time-range -7d
```

### Example 3: Export from US2 Environment

```bash
python export_unparsed_events.py tenant123 logs.txt --environment US2
```

### Example 4: Limit Results

```bash
python export_unparsed_events.py tenant123 logs.txt --max-rows 5000
```

### Example 5: Complete Example

```bash
python export_unparsed_events.py tenant123 sample_logs.txt \
  --environment US1 \
  --time-range -7d \
  --max-rows 10000
```

## Error Handling

The tool handles various error scenarios:

- **File not found**: Clear error message if the output file path is invalid
- **Authentication errors**: Helpful guidance on setting up credentials
- **API errors**: Displays query errors from the Taegis API
- **Network errors**: Reports connection issues
- **No events found**: Gracefully handles empty result sets
- **Missing original_data**: Skips events that don't have an `original_data` field

## Troubleshooting

### "Error: taegis-sdk-python is not installed"

Install the SDK:
```bash
pip install taegis-sdk-python
```

### Authentication Issues

1. Verify your `CLIENT_ID` and `CLIENT_SECRET` are set correctly
2. Check that your credentials have the necessary permissions
3. Try device code authentication if OAuth is not working

### "No events found for the specified tenant and time range"

- Verify the tenant ID is correct
- Try a longer time range (e.g., `-7d` instead of `-1d`)
- Check that there are actually unparsed events in the "generic" schema for that tenant

### "No log sources found"

This means no events were returned from the query. Check:
- The tenant ID is correct
- The time range includes events
- There are unparsed events in the generic schema

### Environment Not Found

Ensure you're using a valid environment identifier (US1, US2, US3, EU, or their aliases).

### Large Result Sets

If you're querying a large time range or have many events:
- Use `--max-rows` to limit the initial query
- The tool will show progress during the query
- Consider using shorter time ranges for initial testing

## Performance Considerations

- **Default max_rows**: Set to 1000 to prevent long-running queries during testing
- **Pagination**: The tool automatically handles pagination for large result sets
- **Memory**: Large exports may consume significant memory; consider using `--max-rows` to limit results

## Related Documentation

- [Taegis SDK for Python Documentation](https://code.8labs.io/platform/sdks/taegis_sdk_python)
- [Taegis API Authentication Guide](https://docs.ctpx.secureworks.com/apis/api_authenticate/)
- [Taegis Events Service](https://code.8labs.io/platform/sdks/taegis_sdk_python)

## License

This tool is provided as-is for use with the Taegis platform.

## Support

For issues related to:
- **This script**: Check the troubleshooting section or file an issue
- **Taegis SDK**: Refer to the SDK documentation
- **Taegis API**: Contact Taegis support

