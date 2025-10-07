# Kumo Take-Home Project

In this project, I took the data given to me and created an AI search and analysis tool for ShopSight that could be easily integrated with Kumo for forecasting. I've created a core flow for the product search that finds the best selling matching product given the query.

## Data Preprocessing

The SQL tables for `articles` and `transactions` were put into the database and are used for product search and retrieving sales data.

## Product Search

Product search is done by taking the user query and using an LLM to develop a SQL query for the relevant. For this iteration the LLM is instructed to intelligently break down the query to filter by the relevant garment group (eg. shoes, dresses) and also search for remaining parts of the query in the product name.

After finding the products that fit the search we will make another query to the database to get the product with the highest sales to show to the user. In the future we could use another LLM to rank the returned products by our own relevance metrics.

The LLM also has an input guardrail that detects queries that aren't about products and early exits the system.

## Past Sales Trends

Given the product ID returned by the product search, we have a straightforward call to our databse that returns the sales history of the product over the span the data (August 2018 to October 2020)

## Forecasted Demand

This value is fixed and mocked. In the future we would use Kumo RFM to generate this value from the sales data we queried previously.

## Customer Segmentation

In parallel to our product search, we run another agent that performs customer segmentation based on the user's query. In the future this agent can be based on the selected product to be more relevant. This agent provides a section that provides the reasoning for the segmentation and also a relevant marketing strategy.

## Stack

- **Frontend:** NextJS App Router
- **Backend:** Fast API
- **Database:** PlanetScale
- **Styling:** Tailwind CSS
- **LLM Agents** Open AI Agents SDK
- **Observability** Maxim AI

## How to Run the Project

### Running the frontend

[Install `pnpm`](https://pnpm.io/installation) and run `pnpm dev`.

### Running the backend

In another tab setup, a python venv, ideally with by [installing `uv`](https://docs.astral.sh/uv/getting-started/installation/) and creating an environment with the `pyproject.yml` file. To run the backend, run `uvicorn main:app --host 0.0.0.0 --port 3000`

## Future Work

- Add unit and integration tests
- Implement access control
- Enhance UI/UX with additional components
- Deploy to cloud hosting platforms
- Integrate CI/CD pipelines
