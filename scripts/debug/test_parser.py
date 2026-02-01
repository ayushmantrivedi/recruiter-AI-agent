import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import asyncio
from app.intelligence.query_parser import query_parser

async def test():
    print("Testing Query Parser...")
    try:
        query = "senior data scientist in bangalore"
        print(f"Parsing: {query}")
        result = await query_parser.parse(query)
        print("Result:", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
