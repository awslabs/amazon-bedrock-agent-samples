import json
import logging
import os
import yfinance as yf
import pandas as pd
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt.risk_models import fix_nonpositive_semidefinite

log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
logging.basicConfig(
    format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

# Supported functions
FUNCTION_NAMES = ["stock_data_lookup", "portfolio_optimization"]


def get_named_parameter(event, name):
    return next(item for item in event["parameters"] if item["name"] == name)["value"]


def stock_data_lookup(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")
    hist = hist.reset_index().to_json(orient="split", index=False, date_format="iso")
    return hist


def build_response(event, responseBody):
    actionGroup = event.get("actionGroup", "")
    function_name = event.get("function", "")
    messageVersion = event.get("messageVersion", "1.0")
    action_response = {
        "actionGroup": actionGroup,
        "function": function_name,
        "functionResponse": {"responseBody": responseBody},
    }
    function_response = {
        "response": action_response,
        "messageVersion": messageVersion,
    }
    logger.info("Function response: {}".format(function_response))
    return function_response


def portfolio_optimization(event):
    logger.info(event)
    parameters = {
        param["name"]: param["value"] for param in event.get("parameters", [])
    }
    tickers = [t.strip() for t in parameters.get("tickers", "").split(",")]
    prices_data_str = parameters.get("prices", "")

    if not tickers or not prices_data_str:
        responseBody = {"TEXT": {"body": "Error: Tickers and prices are required."}}
        return build_response(event, responseBody)

    try:
        raw_prices = json.loads(prices_data_str)
        first_key = next(iter(raw_prices.keys()))
        if first_key in tickers:
            df = pd.DataFrame.from_dict(raw_prices, orient="index").T
        else:
            df = pd.DataFrame.from_dict(raw_prices, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df[tickers]
    except Exception as e:
        logger.error(f"Error processing price data: {str(e)}")
        responseBody = {"TEXT": {"body": "Error: Invalid price data format."}}
        return build_response(event, responseBody)

    logger.info(f"Processed DataFrame:\n{df}")

    mu = expected_returns.ema_historical_return(df)
    S = risk_models.sample_cov(df)
    S = (S + S.T) / 2
    S = fix_nonpositive_semidefinite(S)

    logger.info(f"Expected Returns (mu):\n{mu}")
    logger.info(f"Covariance Matrix (S):\n{S}")

    if mu.isna().any():
        logger.error("Error: Expected returns contain NaN values.")
        responseBody = {
            "TEXT": {
                "body": "Error: Insufficient or invalid data for expected returns."
            }
        }
        return build_response(event, responseBody)

    min_return_threshold = 0.001
    mu_filtered = mu[mu > min_return_threshold]

    if mu_filtered.empty:
        logger.warning(
            "All assets have low returns. Switching to minimum volatility strategy."
        )
        try:
            ef = EfficientFrontier(mu, S)
            ef.min_volatility()
            weights = ef.clean_weights()
        except Exception as e:
            logger.error(f"Error in min_volatility optimization: {str(e)}")
            responseBody = {
                "TEXT": {
                    "body": "Error: Portfolio optimization failed, even with min_volatility fallback."
                }
            }
            return build_response(event, responseBody)
    else:
        try:
            ef = EfficientFrontier(
                mu_filtered, S.loc[mu_filtered.index, mu_filtered.index]
            )
            ef.max_sharpe()
            weights = ef.clean_weights()
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {str(e)}")
            responseBody = {"TEXT": {"body": "Error: Portfolio optimization failed."}}
            return build_response(event, responseBody)

    weights = {k: float(v) for k, v in weights.items()}

    latest_prices = get_latest_prices(df)
    da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=10000)
    allocation, leftover = da.greedy_portfolio()
    allocation = {k: int(v) for k, v in allocation.items()}
    leftover = float(leftover)

    logger.info(f"Optimal Weights: {weights}")
    logger.info(f"Discrete Allocation: {allocation}")
    logger.info(f"Remaining Funds: ${leftover:.2f}")

    response_text = (
        "Optimized Weights: "
        + json.dumps(weights)
        + "; "
        + "Discrete Allocation: "
        + json.dumps(allocation)
        + "; "
        + "Remaining Funds: $"
        + f"{leftover:.2f}"
    )
    responseBody = {"TEXT": {"body": response_text}}
    return build_response(event, responseBody)


def lambda_handler(event, context):
    logging.debug(f"{event=}")
    actionGroup = event.get("actionGroup", "")
    function = event.get("function", "")
    responseBody = {"TEXT": {"body": "Error, no function was called"}}

    logger.info(f"{actionGroup=}, {function=}")

    if function in FUNCTION_NAMES:
        if function == "stock_data_lookup":
            ticker = get_named_parameter(event, "ticker")
            if not ticker:
                responseBody = {"TEXT": {"body": "Missing mandatory parameter: ticker"}}
            else:
                hist = stock_data_lookup(ticker)
                responseBody = {
                    "TEXT": {
                        "body": f"Price history for last 1 month for ticker: {ticker} is as follows:\n{str(hist)}"
                    }
                }
        elif function == "portfolio_optimization":
            return portfolio_optimization(event)
    else:
        responseBody = {"TEXT": {"body": "Invalid Function passed."}}

    action_response = {
        "actionGroup": actionGroup,
        "function": function,
        "functionResponse": {"responseBody": responseBody},
    }
    function_response = {
        "response": action_response,
        "messageVersion": event.get("messageVersion", "1.0"),
    }
    print("Response: {}".format(function_response))
    return function_response
