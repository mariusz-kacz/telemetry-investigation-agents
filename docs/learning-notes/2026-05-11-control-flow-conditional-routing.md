
# Session: Routing

## Goal

Learn LangGraph routing concept

## What I built

Routing mechanism based on input

## LangGraph concept learned

Routing through conditional edges

## Mapping to .NET/C# thinking

In C# terms, this is similar to a state machine transition or a strategy selector. 
The graph state is the workflow context, the node updates that context, and the conditional routing function selects the next activity. 
A fixed edge is like always calling the next handler; a conditional edge is like choosing the next handler based on current workflow state.

## What confused me

## Tradeoffs noticed

Deterministic routing guarantees consistency between executions, LLM is probabilistic so there is no guarantee two executions are going to lead into the same outcome, also LLM is harder to debug and test

add_conditional_edges enables possibility to select dynamically route based on input message

node returns state as it has to update state and leave information which route was selected, conditional router returns a route key to decide which node to select

## Production concerns

## Tests/evals added

## Next step