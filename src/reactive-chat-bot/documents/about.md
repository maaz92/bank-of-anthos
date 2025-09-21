## Flow Description

1. The user starts by sending a natural language query to the UI.

2. The UI forwards this query to the Backend (BE).

3. The Backend prepares the input (including the query, tools, and context) and sends it to the LLM (gemini-2.5-flash).

4. The LLM analyzes the input and plans how to respond.

5. If needed, the LLM calls one or more Tools to gather additional information.

6. The Tools make a REST API call to the bank-of-anthos Microservices (MS).

7. The Microservices return a response to the Tools.

8. The Tools send this response back to the LLM.

9. The LLM generates a final answer and sends it to the Backend.

10. The Backend passes the final answer to the UI.

11. Finally, the UI displays the response to the User.

## Inspiration

Banking often feels complicated and time-consuming. I wanted to create a tool that makes financial services as simple as chatting with a friend.

## What it does

NeoBanker is an AI-powered chatbot that understands natural language. Users can check balances, transfer funds, add recipients just by chatting in plain English.

## How we built it

I built NeoBanker using a large language model (**gemini-2.5-flash**) connected to a backend service. It leverages **bank-of-anthos microservices** through REST APIs for real banking operations, while the UI provides a smooth and intuitive chat experience.

## Challenges we ran into

- Making the chatbot understand complex or ambiguous queries
- Connecting the LLM with multiple backend services in real time
- Ensuring responses remain accurate and relevant to financial tasks

## Accomplishments that we're proud of

- Built a fully working demo that handles real banking queries
- Seamless integration of natural language understanding with banking microservices
- Designed a user-friendly interface that feels natural to interact with

## What we learned

- How to structure prompts and tool usage for reliable LLM outputs
- The importance of error handling when working with multiple services
- How conversational AI can transform traditional customer experiences in banking

## What's next for NeoBanker – modern AI-driven banker

- Expanding to cover more financial services like loan queries and investment advice
- Adding multi-language support for global accessibility
- Strengthening security and compliance for real-world deployment
- Personalizing user experiences with AI-driven financial recommendations
- Expand to voice-based interactions for hands-free banking.
