"""Script de utilidad — ejecutar UNA sola vez para hacer el seed inicial del SAG.

Uso:
    cd backend
    python -m app.agents.sag_seed
"""

import asyncio
from google.cloud import firestore
from app.agents.sag_agent import SagAgent


async def main():
    db    = firestore.AsyncClient()
    agent = SagAgent(db=db)
    result = await agent.run()
    print(f"Seed completado: {result}")


if __name__ == "__main__":
    asyncio.run(main())
