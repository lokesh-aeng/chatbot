import os
from dotenv import load_dotenv
from supabase import create_client,Client
from AI_ChatBot.logging import logger
from AI_ChatBot.components.query_processing import QueryProcessor

from langgraph.graph import END
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage,AIMessage

class RAG:
    def __init__(self,processor:QueryProcessor):
        load_dotenv()
        try: 
            os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
            self.llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        except Exception as e:
            # fall back
            try:
                os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
                self.llm = init_chat_model("llama3-8b-8192", model_provider="groq")
            except:
                try:
                    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
                    self.llm = init_chat_model("gpt-3.5-turbo", model_provider="openai")
                except:
                    raise ValueError("All model initializations failed")
        
        @tool(response_format="content_and_artifact")
        def retrieve(query: str):
            """Retrieve information related to a query."""
            try:
                res = processor.process(query)
                docs = res['retrieved_chunks']
                if not docs:
                    return "", []
                serialized_parts = []
                for doc in docs:
                    meta = doc['metadata'] or {}
                    source = meta.get("filename",'unknown')
                    citation = f"Source: {source}"
                    content = doc['text']
                    serialized_parts.append(f"{citation}\nContent: {content}")
                serialized = "\n\nContext:\n" + "\n\n".join(serialized_parts)
                return serialized, docs
            except Exception as e:
                logger.error(f"Error in retrieve tool: {e}")
                return "", []
        
        self.retrieve = retrieve
    
    
    
    def query_or_respond(self,state: MessagesState):
        """Generate tool call for retrieval or respond."""
        
        llm_with_tools = self.llm.bind_tools([self.retrieve])
        response =  llm_with_tools.invoke(state["messages"])
            
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}
    
    def generate(self,state: MessagesState):
        """Generate answer."""
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_parts = [
            "You are an expert educational assistant for financial markets, Fintech, and AI concepts. Created by Zetheta.",
            "Use the provided context from the organization's knowledge base to answer accurately.",
            "If information is unavailable in the context, indicate that you cannot find it."
            "INSTRUCTIONS: "
                "If the context does not contain the answer, state that the knowledge base does not cover it." 
                "Cite sources in brackets when referencing facts. "
                "Answer clearly and concisely based only on the provided context. "
        ]
        if docs_content:
            system_parts.append("\n Context provided below:")
            system_parts.append(docs_content)
        system_prompt = "\n".join(system_parts)
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_prompt)] + conversation_messages
        try:
            response = self.llm.invoke(prompt)
        except Exception as e:
            logger.error(f"Error in generate node: {e}")
            response = AIMessage(content="I'm sorry, I encountered an error generating the response.")
        return {"messages": [response]}

    def build_graph(self):
        self.graph_builder = StateGraph(MessagesState)
        tools_node = ToolNode([self.retrieve])
        self.graph_builder.add_node(self.query_or_respond)
        self.graph_builder.add_node(tools_node)
        self.graph_builder.add_node(self.generate)

        self.graph_builder.set_entry_point("query_or_respond")
        self.graph_builder.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {END: END, tools_node.name: tools_node.name},
        )
        self.graph_builder.add_edge(tools_node.name, "generate")
        self.graph_builder.add_edge("generate", END)

        graph = self.graph_builder.compile()
        return graph