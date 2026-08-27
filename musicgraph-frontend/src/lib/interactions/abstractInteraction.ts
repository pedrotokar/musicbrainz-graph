import type { GraphEdge, GraphNode, GenericAPIResponse, InteractionOwnedElements, NodeContext, EdgeContext } from "$lib/types";

export abstract class GraphInteraction {
    constructor(
        protected id: string,
        protected interactionAPIResponse: GenericAPIResponse
    ) { }

    getId(): string {
        return this.id;
    }

    //Get the text that is shown to the user to refer to the interaction
    abstract getShowText(): string;

    // Get some node/edge information based on that interaction context. Used 
    // for coloring, tooltips and whatever thing that depends on the node/edge
    // and the interaction
    abstract getNodeContext(node: GraphNode): NodeContext;
    abstract getEdgeContext(edge: GraphEdge): EdgeContext;

    // Get information on whetever the interaction requires a certain node
    // to be always visible. Ideally all interactions should leave at least 
    // one meaningfull node always shown
    abstract shouldAlwaysShowNode(node: GraphNode): boolean;
    abstract shouldAlwaysShowEdge(edge: GraphEdge): boolean;

    getOwnedElements(): GenericAPIResponse {
        return this.interactionAPIResponse
    };
    
    getOwnedElementIds(): InteractionOwnedElements {
        const owned: InteractionOwnedElements = {
            "nodes": [],
            "edges": [],
        }
        if(this.interactionAPIResponse){
            for(const node of this.interactionAPIResponse["nodes"]){
                owned["nodes"].push(node.id);
            }
            for(const edge of this.interactionAPIResponse["edges"]){
                owned["edges"].push(edge.source + "->" + edge.target + "|" + edge.type)
            }
        }
        return owned
    }
}
