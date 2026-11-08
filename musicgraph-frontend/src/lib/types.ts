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

export interface PathAPIResponse extends GenericAPIResponse {
    source: string;
    target: string;
    path: string[];
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
export type NodeContext =
    | { role: "origin" }
    | {
          role: "related";
          referenceNodeId: string; // Expand: origin. Path: previous node.
          edges: GraphEdge[];      // edges between this node and reference node
          pathStep?: { position: number; length: number; isTarget: boolean };
      }
    | { role: "unrelated" };

export type EdgeContext = "forward" | "backward" | "bidirectional" | undefined;


//Relationship management utility types
export interface RelationshipAppearance {
    color: string;
    displayName: string;
}

export type TooltipGenerator = (edge: GraphEdge, sourceName: string, targetName: string) => string;

export type RelationshipConfig = { tooltipGenerator?: TooltipGenerator } & (
    | ({ bidirectional: true } & RelationshipAppearance)
    | { bidirectional: false; forward: RelationshipAppearance; backward: RelationshipAppearance }
);

export type RelationshipRegistry = Record<string, RelationshipConfig>;

export type FilterState = Record<string, 
    | { bidirectional: true; show: boolean }
    | { bidirectional: false; showForward: boolean; showBackward: boolean }
>;

//Search types
export interface SearchResult {
    id: string;
    name: string;
    disambiguation: string | null;
    score: number;
}
