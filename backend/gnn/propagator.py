"""
GNN Propagation Engine

Spreads impact from source nodes to connected nodes using BFS with decay.
M2: The Eyes
"""

import networkx as nx
from typing import List, Tuple, Dict, Any

class GraphPropagator:
    """
    Manages graph structure and signal propagation.
    """
    def __init__(self, decay_factor: float = 0.5, max_hops: int = 2):
        self.graph = nx.Graph()
        self.decay_factor = decay_factor
        self.max_hops = max_hops

    def build_graph(self, edges: List[Tuple[str, str, float]]):
        """
        Build or update graph from edges.
        Edges: (Source, Target, Weight)
        """
        self.graph.clear()
        for u, v, w in edges:
            self.graph.add_edge(u, v, weight=w)

    def propagate(self, source_node: str, initial_impact: float) -> Dict[str, float]:
        """
        Spread impact from a single source node.
        Returns: Dict {Node: AccumulatedImpact}
        """
        impacts = {source_node: initial_impact}
        
        if source_node not in self.graph:
            return impacts
            
        # BFS
        # Queue: (current_node, current_impact, hops)
        queue = [(source_node, initial_impact, 0)]
        visited = {source_node}
        
        while queue:
            current_node, current_impact, hops = queue.pop(0)
            
            if hops >= self.max_hops:
                continue
                
            next_hops = hops + 1
            
            for neighbor in self.graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                    
                edge_data = self.graph.get_edge_data(current_node, neighbor)
                edge_weight = edge_data.get('weight', 1.0)
                
                # Decay logic: Impact * EdgeWeight * DecayFactor
                # Note: Decay is applied at receiver step
                next_impact = current_impact * edge_weight * self.decay_factor
                
                impacts[neighbor] = next_impact
                visited.add(neighbor)
                
                queue.append((neighbor, next_impact, next_hops))
                
        return impacts

    def propagate_batch(self, source_impacts: Dict[str, float]) -> Dict[str, float]:
        """
        Spread impact from multiple sources and aggregate.
        """
        total_impacts = {}
        
        for source, impact in source_impacts.items():
            propagated = self.propagate(source, impact)
            
            for node, value in propagated.items():
                if node not in total_impacts:
                    total_impacts[node] = 0.0
                total_impacts[node] += value
                
        return total_impacts
