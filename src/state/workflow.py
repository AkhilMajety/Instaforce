from langgraph.graph import StateGraph, START, END

from src.state.state import State
from src.llm.model import LLMModel

from src.agents.req_agent import ReqAgent
from src.agents.design_agent import DesignAgent
from src.agents.codegen_agent import CodeGenAgent
from src.agents.deploy_agent import DeployAgent



class WorkflowBuilder:
    """
    Builds the AI-in-Pipeline LangGraph workflow.
    For now the flow is:
    
    START → req_agent → design_agent → codegen_agent → END
    """

    def __init__(self, llm):
        self.llm = llm
        self.graph = StateGraph(State)

    def build_graph(self):
        """
        Build the pipeline up to the code generation agent.
        """

        # Agent instances
        req = ReqAgent(self.llm)
        design = DesignAgent(self.llm)
        codegen = CodeGenAgent(self.llm)
        deployagent = DeployAgent(self.llm)

        # Register nodes
        self.graph.add_node("req_agent", req.process)
        self.graph.add_node("design_agent", design.process)
        self.graph.add_node("codegen_agent", codegen.process)
        self.graph.add_node("deploy_agent", deployagent.process)


        # Edges
        self.graph.add_edge(START, "req_agent")
        self.graph.add_edge("req_agent", "design_agent")
        self.graph.add_edge("design_agent", "codegen_agent")
        self.graph.add_edge("codegen_agent", "deploy_agent")
        self.graph.add_edge("deploy_agent", END)

        return self.graph
    def setup_graph(self):
            
        self.build_graph()

        return self.graph.compile()



llm=LLMModel().get_llm()

graph_builder=WorkflowBuilder(llm)
graph=graph_builder.build_graph().compile()