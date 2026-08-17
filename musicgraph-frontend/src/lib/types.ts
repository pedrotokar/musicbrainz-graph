//TODO: Type everything
//TODO: Change any type to union of known possible types (dates, numbers, strings, ?)

import type { SimulationNodeDatum, SimulationLinkDatum} from 'd3';


//Basic graph types used everywhere
export interface GraphNode {
    id: string;
    display_name: string;
    labels: string[];
    parameters: Record<string, string>;
}

export interface GraphEdge {
    source: string;
    target: string;
    type: string;
    parameters: Record<string, string>;
}

export interface ArtistAdjacentAPIResponse {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

//graph types used in graph rendering
export interface SimulationNode extends GraphNode, SimulationNodeDatum {
}

export interface SimulationEdge extends SimulationLinkDatum<SimulationNode> {
    source: SimulationNode;
    target: SimulationNode;
    type: string;
    parameters: Record<string, string>;
}
