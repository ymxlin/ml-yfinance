import time
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, status, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import logging
import uvicorn
import yfinance as yf
from uvicorn.logging import AccessFormatter



class UserAgentFormatter(AccessFormatter):
    def formatMessage(self, record):
        # The 'scope' contains the raw ASGI request data
        scope = record.args[2]
        headers = dict(scope.get("headers", []))
        
        # Extract User-Agent (headers are bytes in ASGI)
        user_agent = headers.get(b"user-agent", b"-").decode("utf-8")
        
        # Inject a custom attribute into the record
        record.user_agent = user_agent
        return super().formatMessage(record)


# Initialize the FastAPI app
app = FastAPI(
    title="Stock History API",
    description="An API to fetch historical stock data using yfinance.",
    contact={
        "name": "Alvin",
        "email": "y_lin266496@fanshaweonline.ca"
    },
    version="1.0"
)

# 1. CORS Middleware (Essential if your frontend is on a different port/domain)
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:3000"], # Replace with your actual frontend URL
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

yf.config.debug.logging = False


# 2. Custom Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Prevents the browser from "sniffing" the content type (prevents XSS)
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevents your site from being put in an iframe (prevents Clickjacking)
        response.headers["X-Frame-Options"] = "DENY"
        # Enables the browser's built-in XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Forces the use of HTTPS (only use if you have an SSL certificate)
        #response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Controls how much referrer information is shared
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.get("/", response_class=PlainTextResponse, summary="dummy root path")
async def root():
    return "Hello World"


@app.get("/health", response_class=PlainTextResponse, summary="for platform health check")
async def health_check():
    return "OK"


@app.get("/api/stock/{ticker}", summary="yfinance wrapper")
async def get_stock_history(
    ticker: str,
    period: str = Query(
        default="2y", 
        description="Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    )
):
    """
    Fetch historical market data for a given ticker symbol.
    """
    try:
        # Initialize the Ticker object
        stock = yf.Ticker(ticker)
        
        # Fetch the historical data using the specified period
        history_df = stock.history(period=period)
        
        # Handle cases where the ticker is invalid or returns no data
        if history_df.empty:
            raise HTTPException(
                status_code=400, 
                detail=f"No historical data found for ticker '{ticker}' with period '{period}'."
            )
            
        # Convert datetime index to string for clean JSON serialization
        history_df.index = history_df.index.strftime('%Y-%m-%d')
        
        # Convert the Pandas DataFrame to a dictionary
        data_dict = history_df.to_dict(orient="index")

        return JSONResponse(
            content=data_dict,
#            media_type="text/csv",
            headers={}
        )

#        return {
#            "success": True,
#            "ticker": ticker.upper(),
#            "period": period,
#            "rows": len(data_dict),
#            "data": data_dict
#        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        # Catch any unexpected errors from yfinance
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_report_data", summary="Customized endpoint to return assigned data format")
async def get_report_data(
    period: str = Query(
        default="2y",
        description="Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    ),
    norm: str = Query(
        default="y",
        description="Normalized value: y, n"
    )
):
    # 1. Define your list of representative tickers
    tickers = ["QQQ", "VDE", "VEGI", "PBJ", "ICLN", "SPY", "ITA"]

    # 2. Download the data
    # This returns a wide-format DataFrame by default
    data = yf.download(tickers, period=period, keepna=False, auto_adjust=True)
    
    # 3. Extract only the 'Close' prices
    # This removes the multi-level header and keeps tickers as columns
    wide_df = data["Close"]

    if (norm == "y"):
        for t in tickers:
            wide_df[t] = wide_df[t].ffill().bfill()
            wide_df[t] = wide_df[t] / wide_df[t].iloc[0]

    # Convert datetime index to string for clean JSON serialization
    wide_df.index = wide_df.index.strftime('%Y-%m-%d')

    # Convert the Pandas DataFrame to a dictionary
    data_dict = wide_df.to_dict(orient="index")

    return JSONResponse(
        content=data_dict
    )

# For some reason, the ^VIX makes a nan in data. Simply drop the first line to get rid of it.
@app.get("/api/test", summary="A playground to test new features")
async def test():
    # 1. Define your list of representative tickers
    tickers = ["QQQ", "VDE", "VEGI", "^VIX"]

    # 2. Download the data
    # This returns a wide-format DataFrame by default
    data = yf.download(tickers, period="1mo", auto_adjust=True)

    # 3. Extract only the 'Close' prices
    # This removes the multi-level header and keeps tickers as columns
    wide_df = data["Close"]
    print(wide_df.head())
    wide_df.drop(wide_df.index[0], inplace=True)
    print(wide_df.head())

    # Convert datetime index to string for clean JSON serialization
    wide_df.index = wide_df.index.strftime('%Y-%m-%d')

    # Convert the Pandas DataFrame to a dictionary
    data_dict = wide_df.to_dict(orient="index")

    return JSONResponse(
        content=data_dict
    )


app.mount("/", StaticFiles(directory="static", html=True), name="static")


# --- 3. Main Execution Block ---
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        server_header=False,  # Disables "Server: uvicorn"
        date_header=False,    # Disables "Date" header for extra stealth
        proxy_headers=True   # Important for getting real IPs if using a proxy
    )

