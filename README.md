# Octopus API

This is a package for connecting to the Octopus API.

## Usage

```python
from octopusapi.api import OctopusClient

def main():
    client = OctopusClient(apikey=api_key,
                           account="A-16B54A69",
                           postcode="WA46RP",
                           )

main()
```

## Using the api_key

The api key can be stored in a file
