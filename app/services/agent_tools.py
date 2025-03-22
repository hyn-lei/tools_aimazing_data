import logging
import json
from typing import Dict, List, Any, Annotated, TypedDict, Literal, Optional, cast
from pydantic import BaseModel, Field
from langsmith import traceable

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import memory

# LangChain imports
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool

# Project imports
from app.services.web_crawler import WebCrawler
from app.services.ai_analyzer import AIAnalyzer
from app.services.screenshot import ScreenshotService
from app.models.models import DataCategory, AITag
from app.database import db_connection
from config.config import settings


# Define the State Type for the Graph
class AgentState(TypedDict):
    messages: List[Any]  # List of messages exchanged
    url: str  # The URL to analyze
    site_data: Dict[str, str]  # Crawled website data
    analysis_result: Dict[str, Any]  # Analysis results
    screenshot_path: str  # Path to screenshot
    error: str  # Any error that occurred


# Define the Tools for the Agent

class CrawlWebsiteTool(BaseTool):
    name: str = "crawl_website"
    description: str = "Crawl a website and extract its content"
    
    async def _arun(self, url: str) -> Dict[str, str]:
        """Run the tool asynchronously."""
        try:
            crawler = WebCrawler(url)
            site_data = await crawler.crawl()
            if not site_data:
                return {"error": "Failed to crawl website"}
            return {"site_data": site_data}
        except Exception as e:
            logging.error(f"Error crawling website: {str(e)}")
            return {"error": f"Error crawling website: {str(e)}"}

    def _run(self, url: str) -> Dict[str, str]:
        """Run the tool synchronously (not used)."""
        raise NotImplementedError("This tool only supports async execution")


class AnalyzeWebsiteTool(BaseTool):
    name: str = "analyze_website"
    description: str = "Analyze website content and extract structured information"
    
    async def _arun(self, site_data: Dict[str, str]) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        try:
            analyzer = AIAnalyzer()
            analysis_result = await analyzer.analyze(site_data)
            if not analysis_result:
                return {"error": "Failed to analyze content"}
            return {"analysis_result": analysis_result}
        except Exception as e:
            logging.error(f"Error analyzing website: {str(e)}")
            return {"error": f"Error analyzing website: {str(e)}"}

    def _run(self, site_data: Dict[str, str]) -> Dict[str, Any]:
        """Run the tool synchronously (not used)."""
        raise NotImplementedError("This tool only supports async execution")


class TakeScreenshotTool(BaseTool):
    name: str = "take_screenshot"
    description: str = "Take a screenshot of a website"
    
    async def _arun(self, url: str) -> Dict[str, str]:
        """Run the tool asynchronously."""
        try:
            screenshot_service = ScreenshotService()
            screenshot_path = await screenshot_service.take_screenshot(url)
            if not screenshot_path:
                return {"error": "Failed to take screenshot"}
            return {"screenshot_path": screenshot_path}
        except Exception as e:
            logging.error(f"Error taking screenshot: {str(e)}")
            return {"error": f"Error taking screenshot: {str(e)}"}

    def _run(self, url: str) -> Dict[str, str]:
        """Run the tool synchronously (not used)."""
        raise NotImplementedError("This tool only supports async execution")


# Wrapper functions for tools that extract the right parameters from state

@traceable(name="run_crawl_website")
async def run_crawl_website(state: AgentState) -> AgentState:
    """Run the crawl website tool with the appropriate parameters."""
    try:
        url = state.get("url", "")
        if not url:
            return {**state, "error": "No URL provided for crawling"}
            
        tool = CrawlWebsiteTool()
        result = await tool._arun(url=url)
        
        # Update state with result
        if "error" in result:
            return {**state, "error": result["error"]}
        return {**state, "site_data": result.get("site_data", {})}
    except Exception as e:
        logging.error(f"Error in run_crawl_website: {str(e)}")
        return {**state, "error": str(e)}


@traceable(name="run_analyze_website")
async def run_analyze_website(state: AgentState) -> AgentState:
    """Run the analyze website tool with the appropriate parameters."""
    try:
        site_data = state.get("site_data", {})
        if not site_data:
            return {**state, "error": "No site data available for analysis"}
            
        tool = AnalyzeWebsiteTool()
        result = await tool._arun(site_data=site_data)
        
        # Update state with result
        if "error" in result:
            return {**state, "error": result["error"]}
        return {**state, "analysis_result": result.get("analysis_result", {})}
    except Exception as e:
        logging.error(f"Error in run_analyze_website: {str(e)}")
        return {**state, "error": str(e)}


@traceable(name="run_take_screenshot")
async def run_take_screenshot(state: AgentState) -> AgentState:
    """Run the take screenshot tool with the appropriate parameters."""
    try:
        url = state.get("url", "")
        if not url:
            return {**state, "error": "No URL provided for screenshot"}
            
        tool = TakeScreenshotTool()
        result = await tool._arun(url=url)
        
        # Update state with result
        if "error" in result:
            return {**state, "error": result["error"]}
        return {**state, "screenshot_path": result.get("screenshot_path", "")}
    except Exception as e:
        logging.error(f"Error in run_take_screenshot: {str(e)}")
        return {**state, "error": str(e)}


# Agent Processing functions

@traceable(name="process_crawl_result")
async def process_crawl_result(state: AgentState) -> AgentState:
    """Process the crawl result and decide next steps"""
    messages = state.get("messages", [])
    # Check if there was an error in crawling
    if state.get("error"):
        messages.append(AIMessage(content=f"Error during crawling: {state['error']}"))
        return {**state, "messages": messages}
    
    # Process successful crawl
    site_data = state.get("site_data", {})
    if not site_data:
        messages.append(AIMessage(content="No site data was retrieved during crawling."))
        return {**state, "messages": messages, "error": "No site data retrieved"}
    
    num_pages = len(site_data)
    messages.append(AIMessage(content=f"Successfully crawled {num_pages} pages from the website. Proceeding to analyze content."))
    return {**state, "messages": messages}


@traceable(name="process_analysis_result")
async def process_analysis_result(state: AgentState) -> AgentState:
    """Process the analysis result and decide next steps"""
    messages = state.get("messages", [])
    # Check if there was an error in analysis
    if state.get("error"):
        messages.append(AIMessage(content=f"Error during analysis: {state['error']}"))
        return {**state, "messages": messages}
    
    # Process successful analysis
    analysis_result = state.get("analysis_result", {})
    if not analysis_result:
        messages.append(AIMessage(content="No analysis results were generated."))
        return {**state, "messages": messages, "error": "No analysis results"}
    
    messages.append(AIMessage(content=f"Successfully analyzed website content. Extracted information about {analysis_result.get('title', 'Unknown Tool')}. Taking screenshot next."))
    return {**state, "messages": messages}


@traceable(name="process_screenshot_result")
async def process_screenshot_result(state: AgentState) -> AgentState:
    """Process the screenshot result and complete the agent workflow"""
    messages = state.get("messages", [])
    # Check if there was an error in taking screenshot
    if state.get("error"):
        messages.append(AIMessage(content=f"Error during screenshot: {state['error']}"))
        return {**state, "messages": messages}
    
    # Process successful screenshot
    screenshot_path = state.get("screenshot_path", "")
    if not screenshot_path:
        messages.append(AIMessage(content="No screenshot was captured."))
        return {**state, "messages": messages, "error": "No screenshot captured"}
    
    analysis_result = state.get("analysis_result", {})
    title = analysis_result.get("title", "Unknown Tool")
    messages.append(AIMessage(content=f"Successfully captured screenshot for {title}. Analysis complete."))
    return {**state, "messages": messages}


# Agent Router Functions

@traceable(name="process_crawl_router")
def process_crawl_router(state: AgentState) -> str:
    """Route after crawl process."""
    if state.get("error"):
        return "error_handler"
    return "analyze_website"


@traceable(name="process_analysis_router")
def process_analysis_router(state: AgentState) -> str:
    """Route after analysis process."""
    if state.get("error"):
        return "error_handler"
    return "take_screenshot"


@traceable(name="process_screenshot_router")
def process_screenshot_router(state: AgentState) -> str:
    """Route after screenshot process."""
    if state.get("error"):
        return "error_handler"
    return "complete"


# Agent Class Implementation

class URLAnalysisAgent:
    def __init__(self):
        """Initialize the URL Analysis Agent with necessary tools and models"""
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model="google/gemini-flash-1.5",
            temperature=0.2,
            api_key=settings.OPENROUTER_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Create the state graph
        self.workflow = self._build_workflow()
        
        # Create a checkpoint saver for tracing (optional)
        self.memory_saver = memory.MemorySaver()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for URL analysis"""
        # Create a new graph
        workflow = StateGraph(AgentState)
        
        # Add nodes to the graph
        # Tool execution nodes
        workflow.add_node("crawl_website", run_crawl_website)
        workflow.add_node("analyze_website", run_analyze_website)
        workflow.add_node("take_screenshot", run_take_screenshot)
        
        # Processing nodes
        workflow.add_node("process_crawl", process_crawl_result)
        workflow.add_node("process_analysis", process_analysis_result)
        workflow.add_node("process_screenshot", process_screenshot_result)
        
        # Error handling node
        workflow.add_node("error_handler", lambda state: {**state, "messages": state.get("messages", []) + [AIMessage(content="Workflow encountered an error and has stopped.")]})
        
        # Add the end node
        workflow.add_node("complete", lambda state: {**state, "messages": state.get("messages", []) + [AIMessage(content="URL analysis workflow completed successfully.")]})
        
        # Define edges for the workflow
        # Starting edge
        workflow.set_entry_point("crawl_website")
        
        # Main workflow path
        workflow.add_edge("crawl_website", "process_crawl")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "process_crawl",
            process_crawl_router,
            {
                "error_handler": "error_handler",
                "analyze_website": "analyze_website"
            }
        )
        
        workflow.add_edge("analyze_website", "process_analysis")
        
        workflow.add_conditional_edges(
            "process_analysis",
            process_analysis_router,
            {
                "error_handler": "error_handler",
                "take_screenshot": "take_screenshot"
            }
        )
        
        workflow.add_edge("take_screenshot", "process_screenshot")
        
        workflow.add_conditional_edges(
            "process_screenshot",
            process_screenshot_router,
            {
                "error_handler": "error_handler",
                "complete": "complete"
            }
        )
        
        # End nodes
        workflow.add_edge("error_handler", END)
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Analyze a URL using the agent workflow
        
        Args:
            url: The URL to analyze
            
        Returns:
            A dictionary containing the analysis results, screenshot path, and any errors
        """
        try:
            # Initialize state
            initial_state = {
                "messages": [
                    SystemMessage(content="You are an AI assistant analyzing a website."),
                    HumanMessage(content=f"Please analyze the website at {url}")
                ],
                "url": url,
                "site_data": {},
                "analysis_result": {},
                "screenshot_path": "",
                "error": ""
            }
            
            # Execute the workflow
            result = await self.workflow.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": f"url_analysis_{url}"}}
            )
            
            # Check for errors
            if result.get("error"):
                logging.error(f"Error in URL analysis workflow: {result['error']}")
                return {"error": result["error"]}
            
            # Return the results
            return {
                "analysis_result": result.get("analysis_result", {}),
                "screenshot_path": result.get("screenshot_path", ""),
                "messages": [m.content for m in result.get("messages", [])]
            }
            
        except Exception as e:
            logging.error(f"Error in analyze_url: {str(e)}", exc_info=True)
            return {"error": str(e)}
