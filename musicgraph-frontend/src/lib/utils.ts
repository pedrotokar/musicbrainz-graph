import type { GraphEdge, SimulationEdge } from './types';

export function getEdgeId(edge: GraphEdge | SimulationEdge): string {
    const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
    const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
    return `${sourceId}->${targetId}|${edge.type}`;
}

export const edgeKey = getEdgeId;
