
import sys
import os
import asyncio

sys.path.append(os.getcwd())

async def run_debug():
    print("DEBUG START")
    try:
        from app.services.pipeline import RecruiterPipeline
        print("Imported RecruiterPipeline")
        
        pipeline = RecruiterPipeline()
        print("Instantiated RecruiterPipeline")
        
        await pipeline.initialize()
        print("Initialized Pipeline")
        
        if hasattr(pipeline, "intelligence_engine"):
            print("check: intelligence_engine PRESENT")
        else:
            print("check: intelligence_engine MISSING")
            
        if hasattr(pipeline, "concept_reasoner"):
            print("check: concept_reasoner PRESENT (BAD)")
        else:
            print("check: concept_reasoner MISSING (GOOD)")
            
        print("DEBUG COMPLETE")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
