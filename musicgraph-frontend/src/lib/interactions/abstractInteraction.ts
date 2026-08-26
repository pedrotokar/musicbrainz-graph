import type { GraphEdge, GraphNode, GenericAPIResponse, InteractionOwnedElements, NodeContext, EdgeContext } from "$lib/types";

export abstract class GraphInteraction {
    constructor(
        protected id: string,
        protected interactionAPIResponse: GenericAPIResponse
    ) { }

    getId(): string {
        return this.id;
    }

    //TODO: improve edge context if I decide to go that way
    abstract getShowText(): string;
    abstract getNodeContext(nodeId: string): NodeContext;
    abstract getEdgeContext(edge: GraphEdge): EdgeContext;
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
