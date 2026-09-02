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

export interface GenericAPIResponse {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

export interface InteractionOwnedElements {
    nodes: string[];
    edges: string[];
}


//Graph types used in graph rendering
export interface SimulationNode extends GraphNode, SimulationNodeDatum {}

export interface SimulationEdge extends SimulationLinkDatum<SimulationNode> {
    source: SimulationNode;
    target: SimulationNode;
    type: string;
    parameters: Record<string, string>;
}

//Node context returned by interactions
export interface NodeContext {
    isOrigin: boolean;
    isRelated: boolean;
    edges: GraphEdge[];
}

export type EdgeContext = "forward" | "backward" | "bidirectional" | undefined;


//Relationship management utility types
export interface RelationshipDictionary {
    color: string;
    displayName: string;
}


export type RelationshipConfig = 
    | ({ bidirectional: true } & RelationshipDictionary)
    | { bidirectional: false; forward: RelationshipDictionary; backward: RelationshipDictionary };

export type RelationshipRegistry = Record<string, RelationshipConfig>;

export type FilterState = Record<string, 
    | { bidirectional: true; show: boolean }
    | { bidirectional: false; showForward: boolean; showBackward: boolean }
>;
