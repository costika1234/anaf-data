import json
import requests
import sys
import time

from datetime import datetime

PATH_TO_CUIS = 'cuis.txt'
PATH_TO_ANAF_DATA = 'anaf-data.json'

ANAF_URL = 'https://webservicesp.anaf.ro/PlatitorTvaRest/api/v8/ws/tva'

# ANAF restrictions: at most 1 request per second,
# with every request containing at most 100 CUIs.
BATCH_SIZE = 50

# Wait time before sending the next request (expressed in seconds).
WAIT_TIME = 5

# Maximum number of retries (per request).
MAX_RETRIES = 5

# Maximum number of total retries.
MAX_IS_DOWN = 10


def get_anaf_dict(cui):
    return {
        'cui': cui,
        'data': datetime.now().strftime('%Y-%m-%d')
    }


def wait_or_print(attempt):
    if attempt < MAX_RETRIES:
        # Wait before sending the request again.
        time.sleep(WAIT_TIME)
    else:
        print('❌ Max retries reached. Operation failed.')


def get_anaf_data(cui_or_cuis):
    payload_list = []

    if type(cui_or_cuis) == list:
        for cui in cui_or_cuis:
            payload_list.append(get_anaf_dict(cui))
    else:
        payload_list.append(get_anaf_dict(cui_or_cuis))

    response = ''
    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            response = requests.post(
                ANAF_URL,
                headers={
                    'Content-Type': 'application/json'
                },
                data=json.dumps(payload_list)
            )

            # Note that ANAF response might be empty.
            if response:
                break
            else:
                attempt += 1
                print('❌ Empty response. Retrying...')
                wait_or_print(attempt)

        # Catch connection-related exceptions here.
        except BaseException as e:
            attempt += 1
            print('❌ Connection failure. Retrying...')
            wait_or_print(attempt)

    return response.text if response else ''


def dump_anaf_data(company_codes):
    # Remove potential duplicates from the input list.
    company_codes = list(dict.fromkeys(company_codes))

    anaf_data = []
    is_down_counter = 0
    company_codes_no = len(company_codes)

    for i in range(0, company_codes_no, BATCH_SIZE):
        cuis = company_codes[i:i + BATCH_SIZE]
        curr_anaf_data = get_anaf_data(cuis)
        attempt = 0

        # Retry as long as we receive bad responses.
        while (
            (
                is_down := ('Mentenanta sistem' in curr_anaf_data) or
               '404 Not Found' in curr_anaf_data
            ) and attempt < MAX_RETRIES
        ):
            if is_down_counter == MAX_IS_DOWN:
                print('❌ ANAF is down. Exiting...')
                sys.exit(0)

            if is_down:
                is_down_counter += 1
                print('🌀 Service down. Retrying...')
            else:
                print('🌀 404. Retrying...')

            time.sleep(WAIT_TIME)
            curr_anaf_data = get_anaf_data(cuis)
            attempt += 1

        if attempt == MAX_RETRIES:
            print('❌ Unable to fetch ANAF data for:', cuis)
        else:
            # This happens in case we send invalid CUIs in a batch.
            if 'contine date incorecte!!!!' in curr_anaf_data:
                print('❌ Invalid CUIs:', cuis)

            # The only case in which the request succeeded.
            else:
                # Reset the down counter.
                is_down_counter = 0

                cuis_no = min(BATCH_SIZE, len(cuis))
                cui_str = 'CUI' if cuis_no == 1 else 'CUIs'
                print(f'✅ Added {cuis_no} {cui_str}...')

                # Convert the current ANAF data to JSON (if possible).
                try:
                    anaf_data.append(json.loads(curr_anaf_data))
                except json.JSONDecodeError:
                    anaf_data.append(f'Decode error: "{curr_anaf_data}".')

        # Only wait when a non-final batch is completed.
        if i != company_codes_no - BATCH_SIZE and len(cuis) == BATCH_SIZE:
            time.sleep(WAIT_TIME)

    # Dump the data to a file (JSON format).
    with open(PATH_TO_ANAF_DATA, 'w') as f:
        json.dump(anaf_data, f, indent=4)


def main():
    # Use command line args as CUIs (if any).
    if len(sys.argv) > 1:
        company_codes = sys.argv[1:]

    # Otherwise, use the CUIs from the input file.
    else:
        with open(PATH_TO_CUIS) as f:
            company_codes = [line.strip() for line in f]

    dump_anaf_data(company_codes)


if __name__ == '__main__':
    main()
