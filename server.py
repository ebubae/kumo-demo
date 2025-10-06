from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agents import trace
import asyncio
from mysql.connector import connect
import json

from agent import customer_segmenter, product_search
from env import DB_CONFIG
from queries import PREV_MONTH_QUERY, TOP_PRICE_QUERY

app = FastAPI()
connection = connect(**DB_CONFIG)

def abbreviate_number(num):
    if abs(num) >= 1e6:
        return f"{num/1e6:.1f}M"
    if abs(num) >= 1e3:
        return f"{num/1e3:.1f}K"
    return str(num)

async def stream_analytics(query: str):
    with trace("Kumo Agent Workflow"):
        customer_segments_task = asyncio.create_task(customer_segmenter(query))
        connection.reconnect()
        cursor = connection.cursor()
        # Step 1: Yield product or error
        product = await product_search(query)
        if not product:
            yield json.dumps({"error": "No product found."}) + "\n"
            return
        db_result = product[0]["db_result"]
        if not db_result:
            yield json.dumps({"error": "No product found."}) + "\n"
            return
        # TODO: Use LLM to rank results
        if len(db_result) > 1:
            print("multiple results, picking top one")
            top_seller_query = TOP_PRICE_QUERY.format(",".join([str(p["product_id"]) for p in db_result]))
            cursor.execute(top_seller_query)
            top_seller_id = cursor.fetchall()
            top_seller_id = top_seller_id[0][0]
            product = [p for p in db_result if p["product_id"] == top_seller_id][0]
        else:
            product = db_result[0]
        yield json.dumps(product) + "\n"

        # Step 2: Simulate AI agent calls for dashboard data
        product_id = product["product_id"]
        sales_query = PREV_MONTH_QUERY.format(product_id)
        cursor.execute(sales_query)
        sales_results = cursor.fetchall()
        # Return only the sales number in a list
        sales_results = [row[1] for row in sales_results]
        print(sales_results)
        customer_segments = await customer_segments_task
        print("Customer segments", customer_segments)
        dashboard_data = {
            "sales_trends": sales_results,
            # TODO: Use Kumo RFM to forecase demand
            "forecasted_demand": 4200000,
            "forecast_text": "Expected increase in demand for next quarter.",
            "customer_segments": [segment.model_dump() for segment in customer_segments],
        }
        cursor.close()
        yield json.dumps(dashboard_data) + "\n"


@app.get("/api/analytics")
async def index(query: str = ""):
    async def event_stream():
        async for chunk in stream_analytics(query):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
