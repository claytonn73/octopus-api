# Octopus API

This is a package for connecting to the Octopus API.

## Usage

```python
from octopusapi.api import OctopusClient

async def main():
    client = OctopusClient(apikey=api_key,
                           account="A-xxBxxAxx",
                           postcode="xxx xxx",
                           )

asyncio.run(main())
```

## Using the api_key

The api key can be stored in a file
