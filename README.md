# anaf-data
A Python script that retrieves data about Romanian companies using the official ANAF API. Requires the [`requests`](https://requests.readthedocs.io/en/latest/) library.

# Usage
Company registration codes (also known as CUIs in Romania) can be supplied either on the command line or in the `cuis.txt` input file.

## CUIs provided on the command line
```python main.py 14399840 2864518 2816464```

## CUIs read from the input file
```python main.py```

## Output
If successful, the script writes company data for the given CUIs in the `anaf-data.json` output file.

# Additional considerations
The script uses some parameters to control the number of CUIs sent in a request as well as the wait time between requests and the number of retries.

```python
# ANAF restrictions: at most 1 request per second,
# with every request containing at most 100 CUIs.
BATCH_SIZE = 50

# Wait time before sending the next request (expressed in seconds).
WAIT_TIME = 5

# Maximum number of retries (per request).
MAX_RETRIES = 5

# Maximum number of total retries.
MAX_IS_DOWN = 10
```
