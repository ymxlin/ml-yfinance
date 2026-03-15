# ml-yfinance

In this project, it's an easy structure to quickly launch a website with basic possible security features.

Highlights

  1. leverage tailnet + ufw combo to hide ssh entrance from internet.
  2. use uvicon that offers simple http capability.
  3. systemd enabled script that simplifies server maintenance
  4. logrotate enabled
  5. fail2ban enabled (testing since 13-Mar-26)
  6. use FastAPI to quickly put together API endpoints and data.
    - /docs for swagger UI
    - /openapi.json for structure
    - redoc for an alternative UI

References

  * [FastAPI](https://fastapi.tiangolo.com/)
  * [API Document](https://ranaroussi.github.io/yfinance/reference/index.html)
  * [Yahoo Finance Dashboard](https://ca.finance.yahoo.com/)
