from agents import Agent, InputGuardrail, GuardrailFunctionOutput, \
    ModelSettings, RunContextWrapper, Runner, function_span, \
    add_trace_processor
from agents.exceptions import InputGuardrailTripwireTriggered, ModelBehaviorError
from env import MAXIM_API_KEY, MAXIM_REPO_ID, connection
from maxim import Maxim
from maxim.logger.openai.agents import MaximOpenAIAgentsTracingProcessor
from prompts import CUSTOMER_SEGMENTER_PROMPT, PRODUCT_CHECK_PROMPT, PRODUCT_SQL_MAPPER
from pydantic import BaseModel
from sql_metadata import Parser

# Integrate with Maxim AI for observability
logger = Maxim({'api_key': MAXIM_API_KEY}).logger({'id': MAXIM_REPO_ID})
add_trace_processor(MaximOpenAIAgentsTracingProcessor(logger))

AVAILABLE_TABLES = ["articles", "customers", "transactions"]

class ProductCheckOutput(BaseModel):
    is_product_query: bool
    reasoning: str

class SQLQuery(BaseModel):
    info_to_retrieve: str
    raw_sql_query: str

class Product(BaseModel):
    product_id: int
    product_name: str
    image_url: str

class DatabaseResponse(BaseModel):
    info_to_retrieve: str
    tables: list[str]
    columns: list[str]
    db_result: list[Product]

class CustomerSegment(BaseModel):
    segment_name: str
    reasoning: str
    marketing_strategy: str

input_guardrail_agent = Agent(
    name="Product check",
    instructions=PRODUCT_CHECK_PROMPT,
    output_type=ProductCheckOutput,
    model="gpt-4.1-mini",
)

async def product_guardrail(ctx: RunContextWrapper, agent, input_data):
    result = await Runner.run(input_guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(ProductCheckOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_product_query,
    )

def get_product_data(context: list[SQLQuery]) -> list[DatabaseResponse]:
    """Runs inputted SQL string to return relevant product data."""
    connection.reconnect()
    cursor = connection.cursor()
    full_response = []
    try:
        for query in context:
            print("opening DB connection to planetscale")
            print(f"executing query: {query.raw_sql_query}")
            cursor.execute(query.raw_sql_query)
            results = cursor.fetchall()
            results = [Product(
                product_id=row[0],
                product_name=row[1],
                image_url=row[2],
            ) for row in results]
            print(f"DB results: {results}")
            parser = Parser(query.raw_sql_query)
            full_response.append(DatabaseResponse(
                info_to_retrieve=query.info_to_retrieve,
                db_result=results,
                tables=parser.tables,
                columns=parser.columns,
            ).model_dump())
        cursor.close()
        return full_response
    except Exception as e:
        print("error running tool")
        print(e)
        raise ModelBehaviorError("Call to DB failed")

schema_mapper = Agent(
    name="Schema Mapper",
    instructions=PRODUCT_SQL_MAPPER,
    output_type=list[SQLQuery],
    model_settings=ModelSettings(temperature=0.2, top_p=0.2),
    input_guardrails=[
        InputGuardrail(guardrail_function=product_guardrail),
    ]
)

customer_segment = Agent(
    name="Customer Segmenter",
    instructions=CUSTOMER_SEGMENTER_PROMPT,
    output_type=list[CustomerSegment],
)

async def customer_segmenter(user_input: str) -> list[CustomerSegment]:
    result = await Runner.run(customer_segment, user_input)
    return result.final_output

async def product_search(user_input: str):
    # Run the query rewriter to get SQL queries
    try:
        query_result = await Runner.run(schema_mapper, user_input)
        sql_queries: list[SQLQuery] = query_result.final_output
        print("SQL Queries", sql_queries)
        if any(query.raw_sql_query for query in sql_queries):
            with function_span("get_product_data") as span:
                span.span_data.input = str(sql_queries)
                tables = [Parser(query.raw_sql_query).tables for query in sql_queries]
                tables = [t for tt in tables for t in tt]
                print("tables", tables)
                if any(table not in AVAILABLE_TABLES for table in tables):
                    print("no available tables")
                    span.set_error("Attempted to call tables that do not exist")
                    raise ModelBehaviorError("Calling imaginary tables")
                print("calling DB")
                db_result = get_product_data(sql_queries)
                print("RESULT", db_result)
                span.span_data.output = db_result
                return db_result
            return {}
    except InputGuardrailTripwireTriggered as e:
        print("Query not about a product", e.guardrail_result.output.output_info)
        return {}
