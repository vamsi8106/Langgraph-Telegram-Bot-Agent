# # src/app/main.py
# import logging
# from dotenv import load_dotenv

# # 1) Load env FIRST so settings picks them up
# load_dotenv()

# from .config.logging import configure_logging
# from .config.settings import settings
# from .di import build_container
# from .workflows.karan_graph import build_graph
# from .telemetry import init_telemetry  # unified tracing + metrics
# from langchain_core.messages import HumanMessage

# def main():
#     configure_logging()
#     init_telemetry()  # starts tracing (if enabled) + Prometheus server (if enabled)

#     # (DEV ONLY) Ensure tables exist if you aren't using Alembic locally
#     if settings.env == "dev":
#         try:
#             from .db import Base, engine
#             Base.metadata.create_all(bind=engine)
#         except Exception:
#             # If Alembic manages migrations, ignore failures here.
#             pass

#     log = logging.getLogger("app")
#     log.info("Starting Karan Bot | env=%s debug=%s", settings.env, settings.debug)

#     c = build_container()
#     graph = build_graph(c)

#     out = graph.invoke(
#         {"messages": [HumanMessage(content="hey karan, how's the summit?")]},
#         {"configurable": {"thread_id": "local_v2"}}
#     )
#     log.info("Graph output keys: %s", list(out.keys()))
#     log.info("Ready.")

# if __name__ == "__main__":
#     main()

# src/app/main.py
"""
Local bootstrap for the Karan bot.

- Loads environment variables early (dotenv)
- Configures logging and unified telemetry (tracing + Prometheus)
- (Dev only) Ensures DB tables exist if Alembic isn't used
- Builds the DI container + graph and performs a quick sanity invoke
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from .config.logging import configure_logging
from .config.settings import settings
from .di import build_container
from .telemetry import init_telemetry  # unified tracing + metrics
from .workflows.karan_graph import build_graph


# Load env FIRST so `settings` picks them up.
load_dotenv()


def main() -> None:
    """
    Entry point for local runs and smoke testing.
    """
    # Logging + telemetry (Prometheus server if enabled)
    configure_logging()
    init_telemetry()

    # (DEV ONLY) Optionally create tables without Alembic
    if settings.env == "dev":
        try:
            from .db import Base, engine
            Base.metadata.create_all(bind=engine)
        except Exception:
            # If Alembic manages migrations, ignore failures here.
            pass

    log = logging.getLogger("app")
    log.info("Starting Karan Bot | env=%s debug=%s", settings.env, settings.debug)

    # Build DI + graph
    container = build_container()
    graph = build_graph(container)

    # Quick smoke invoke to verify graph wiring
    out = graph.invoke(
        {"messages": [HumanMessage(content="hey karan, how's the summit?")]},
        {"configurable": {"thread_id": "local_v2"}},
    )
    log.info("Graph output keys: %s", list(out.keys()))
    log.info("Ready.")


if __name__ == "__main__":
    main()
